import traceback

import requests
from dotenv import load_dotenv

load_dotenv()
import asyncio
import copy
import json
import os
import re
import threading
import time
import uuid

from utils import getLogger

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
WPS_SID = os.environ["WPS_SID"]
WPS_SID_TEST = os.environ["WPS_SID_TEST"]
import urllib3

# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import sseclient


def get_test_url(url):
    return url.replace("lingxi.wps.cn", "120.92.124.158")
    # return url.replace("copilot.wps.cn", "copilot.wps.cn")


def get_headers(is_test, model_url, search_engines, wps_sid):
    if not wps_sid:
        wps_sid = WPS_SID_TEST if is_test else WPS_SID
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0 rfc/1.0",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://lingxi.wps.cn/",
        "Origin": "https://lingxi.wps.cn",
        "Connection": "keep-alive",
        "Cookie": (
            f"wps_sid={wps_sid};debug_api=1;search_engines={search_engines}"
            if is_test
            else f"wps_sid={wps_sid};debug_api=1"
        ),
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Priority": "u=1",
        "X-Cc-Version": "1",
    }
    if is_test:
        headers["Host"] = "lingxi.wps.cn"
    if model_url:
        headers["Cookie"] = headers["Cookie"] + f";model_url={model_url}"
    return headers


class Copilot:
    def __init__(
        self,
        is_test=True,
        model_url="",
        custom_headers={},
        search_engines="",
        wps_sid="",
        agent="",
    ):
        self.is_test = is_test
        self.model_url = model_url
        self.request_sesion = requests.Session()
        self.session_id = None
        self.headers = get_headers(is_test, model_url, search_engines, wps_sid)
        self.request_sesion.headers.update(self.headers)
        self.request_sesion.headers.update(custom_headers)
        self.request_sesion.verify = False
        self.host = "120.92.124.158" if self.is_test else "lingxi.wps.cn"
        self.agent = agent

    def create_session(self, payload={}):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions"
        response = self.request_sesion.post(url, json=payload)
        res = response.json()
        # print(url)
        # print("Request Headers:", response.request.headers)
        # print(response)
        # print(res)
        if res.get("data") and res.get("data").get("session_id"):
            print("session_id", res["data"]["session_id"])
            return res["data"]["session_id"]
        else:
            print(f"创建session失败: {response.text}")
            return None

    def question(self, session_id, question, context_file_id=None, agent=None):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/completions"
        if type(question) == str:
            data = {
                "question": question,
                "context": {},
                "quote_files": [],
                "file_ids": [],
                # "reasoning": True,
                # "thinking": "enabled",
            }
        else:
            data = question
        if self.agent and not agent:
            agent = self.agent
        if not data.get("context"):
            data["context"] = {"agent": agent}
        if "agent" not in data["context"]:
            data["context"]["agent"] = agent
        if context_file_id:
            data["context"]["file_id"] = {"id": context_file_id, "type": "file"}
        # print(44444, data)
        if "card_type" in data:
            del data["card_type"]
        response = None  # Initialize response to avoid being unbound
        data_str = json.dumps(data, ensure_ascii=False)[:1000]
        try:
            response = self.request_sesion.post(url, json=data, stream=True)
            response.raise_for_status()
            response.encoding = "utf-8"

            # 流式处理响应
            full_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    full_response += line + "\n"

                    # 检查是否包含 client_operation，如果是则解析并调用notify
                    if (
                        '"type":"client_operation"' in line
                        or '"type": "client_operation"' in line
                    ):
                        print("检测到 client_operation，解析operation_id")
                        try:
                            # 尝试解析JSON数据
                            if line.startswith("data:"):
                                json_str = line[5:]  # 去掉 "data:" 前缀
                            else:
                                json_str = line

                            data_obj = json.loads(json_str)
                            if (
                                data_obj.get("data", {}).get("operation_type")
                                == "ppt_set_font"
                            ):
                                operation_id = data_obj["data"]["operation_id"]
                                print(f"提取到 operation_id: {operation_id}")

                                # 调用 notify_async 并传入提取的 operation_id
                                notify_data = {
                                    "operation_id": operation_id,
                                    "operation_type": "ppt_set_font",
                                    "metadata": {
                                        "code": "001004000",
                                        "result": True,
                                        "message": "全文字体已统一，请问还有什么需要调整或帮忙的？",
                                    },
                                }
                                self.notify_async(
                                    session_id=session_id, data=notify_data, delay=0
                                )
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"解析 client_operation 数据失败: {e}")

            logger.debug(
                f'---req-start---\nlink: https://lingxi.wps.cn/chat/{session_id}\nurl: {url}\n:payload: {data_str}\nx-request-id: {response.headers["x-request-id"]}\nresponse_headers: {response.headers}\nresponse: {full_response}\n---req-end---\n\n\n'
            )
            return full_response, response.headers["x-request-id"]
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if response:
                logger.debug(
                    f'---req-start---\n https://lingxi.wps.cn/chat/{session_id}\n:{url}\n:{data_str}\n:{response.headers.get("x-request-id", "N/A")}\n:{response.text if response else "N/A"} ]]]---req-end---\n\n\n'
                )
                return response.text, response.headers.get("x-request-id", "N/A")
            else:
                logger.debug(
                    f"---req-start---\n https://lingxi.wps.cn/chat/{session_id}\n:{url}\n:{data_str}\n:N/A\n:N/A ]]]---req-end---\n\n\n"
                )
                return "event:error", session_id

    def deepresearch_completion(self, session_id, question):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}//expert_completion"
        if type(question) == str:
            data = {
                "question": question,
                "file_ids": [],
                "upload_ids": [],
                "collect_ids": [],
                "official_doc_ids": [],
                "thinking": "disabled",
                "with_mcp": False,
                "with_expert": True,
                "command": "",
            }
        else:
            data = question

        response = None  # Initialize response to avoid being unbound
        data_str = json.dumps(data, ensure_ascii=False)[:1000]
        try:
            response = self.request_sesion.post(url, json=data, stream=True)
            response.raise_for_status()
            response.encoding = "utf-8"

            # 流式处理响应
            full_response = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    full_response += line + "\n"
            logger.debug(
                f'---req-start---\nlink: https://lingxi.wps.cn/chat/{session_id}\nurl: {url}\n:payload: {data_str}\nx-request-id: {response.headers["x-request-id"]}\nresponse_headers: {response.headers}\nresponse: {full_response}\n---req-end---\n\n\n'
            )
            return full_response, response.headers["x-request-id"]
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if response:
                logger.debug(
                    f'---req-start---\n https://lingxi.wps.cn/chat/{session_id}\n:{url}\n:{data_str}\n:{response.headers.get("x-request-id", "N/A")}\n:{response.text if response else "N/A"} ]]]---req-end---\n\n\n'
                )
                return response.text, response.headers.get("x-request-id", "N/A")
            else:
                logger.debug(
                    f"---req-start---\n https://lingxi.wps.cn/chat/{session_id}\n:{url}\n:{data_str}\n:N/A\n:N/A ]]]---req-end---\n\n\n"
                )
                return "event:error", session_id

    def history(self, session_id):
        url = (
            f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/messages"
        )
        history_data = self.request_sesion.get(url).json()
        logger.debug(history_data)
        try:
            new_history = {
                "data": {"list": [entry for entry in history_data["data"]["list"]]},
                "result": history_data["result"],
            }
        except KeyError as e:
            print(f"KeyError: {e}")
            new_history = history_data
        return new_history

    def get_last_group_id(self, session_id):
        history = self.history(session_id)
        return history.get("data").get("list")[-1]["group_id"]  # type: ignore

    def get_last_message_id(self, session_id):
        history = self.history(session_id)
        return history.get("data").get("list")[-1]["message_id"]  # type: ignore

    def notify_async(
        self,
        session_id,
        data={
            "operation_id": "8899113005494357087",
            "operation_type": "ppt_set_font",
            "metadata": {
                "code": "001004000",
                "result": True,
                "message": "全文字体已统一，请问还有什么需要调整或帮忙的？",
            },
        },
        delay=3,
    ):
        """异步调用 notify 方法"""

        def _notify():
            if delay:
                time.sleep(delay)
            url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/notify"
            response = self.request_sesion.post(url, json=data)
            response.encoding = "utf-8"
            print(111, response.text, response.headers["x-request-id"])
            # response.raise_for_status()

            return response.text, response.headers["x-request-id"]

        # 在新线程中执行 notify
        thread = threading.Thread(target=_notify)
        thread.daemon = True
        thread.start()

    def questions(
        self,
        questions,
        context_file_id=None,
        with_history=True,
        session_id=None,
        agent=None,
    ):
        # print(questions)
        if not session_id:
            session_id = None
            max_retries = 3
            while session_id is None and max_retries > 0:
                try:
                    max_retries = max_retries - 1
                    session_id = self.create_session()
                except Exception as e:
                    print(f"创建session失败: {e}")
            if session_id is None:
                return None
        rs = []

        for q in questions:
            card_type = q.get("card_type", "")
            if "card_type" in q:
                del q["card_type"]
            # print(222, card_type, q)
            r = self.question(
                session_id, q, context_file_id=context_file_id, agent=agent
            )
            rs.append(r)
            time.sleep(0.3)
            if card_type == "ppt":
                card = self.generate_ppt_all(session_id)
                rs.append(("ppt", card))
        return (
            self.history(session_id) if with_history else "",
            rs,
            session_id,
        )

    def deepresearches(
        self,
        questions,
        with_history=True,
        session_id=None,
    ):
        # print(questions)
        if not session_id:
            session_id = None
            max_retries = 3
            while session_id is None and max_retries > 0:
                try:
                    max_retries = max_retries - 1
                    session_id = self.create_session({"session_mode": "expert"})
                except Exception as e:
                    print(f"创建session失败: {e}")
            if session_id is None:
                return None
        rs = []

        for q in questions:
            # print(222, card_type, q)
            r = self.deepresearch_completion(
                session_id,
                q,
            )
            rs.append(r)
            time.sleep(0.3)
        return (
            self.history(session_id) if with_history else "",
            rs,
            session_id,
        )

    def download_file(self, session_id, cc_file_id, filepath):
        resp1 = self.request_sesion.get(
            f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/images/gen_image/{cc_file_id}?max_edge=40000",
        ).json()
        url = resp1.get("data", {}).get("url")
        print(f"Downloading file from URL: {url}")
        if url:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)

    def prepare_card_data(self, card_data_resp):
        slides = (
            card_data_resp.get("data", {})
            .get("card_data", {})
            .get("ppt_outline_structure", [])
            .get("slide", [])
        )
        text = slides[0]["titles"][0]["value"]
        root_node = {
            "node_type": "nt_span",
            "text": text,
            "children": [],
        }
        contents = [f"# {text}"]
        for slide in slides:
            if slide["type"] == "chapter":
                text = slide["titles"][0]["value"]
                root_node["children"].append(
                    {
                        "id": slide.get("id", ""),
                        "node_type": "nt_span",
                        "text": text,
                        "level": 0,
                    }
                )
                contents.append(f"## {text}")

        return {
            "content": "\n\n".join(contents),
            "outlines": {
                "root_node": root_node,
            },
        }

    def parse_ppt_body(self, response_text):
        chapters = {}
        for line in response_text.splitlines():
            if line.startswith("data:"):

                json_str = line[5:]
                logger.info(f"json_str: {json_str}")
                try:
                    # 如果为空，则跳过
                    if not json_str or json_str.strip() == "":
                        continue

                    obj = json.loads(json_str)
                    data = obj.get("data", "{}")
                    try:
                        data = json.loads(data) if isinstance(data, str) else {}
                    except json.JSONDecodeError:
                        print(f"解析 data JSON 数据失败: {data}")
                        data = {}
                    logger.info(f"data2: {data}")
                    content = data.get("content", "")
                    chapter_id = data.get("chapter_id", "")
                    if not chapter_id:
                        continue
                    logger.info(f"line parse: {chapter_id} {content}")
                    if chapter_id not in chapters:
                        chapters[chapter_id] = ""

                    chapters[chapter_id] += content
                except json.JSONDecodeError:
                    print(f"解析 JSON 数据失败: {json_str},{traceback.format_exc()}")
                except Exception as e:
                    print(f"其他数据失败: {json_str} ,{str(e)}")

        id_childrens = {}
        for chapter_id, content in chapters.items():
            childrens = id_childrens.get(chapter_id, [])
            id_childrens[chapter_id] = childrens

            cur_level1 = None
            cur_level2 = None
            for line in content.splitlines():
                if line.startswith("### "):
                    content = line.strip().replace("### ", "")
                    cur_level1 = {
                        "node_type": "nt_span",
                        "text": content,
                        "level": 1,
                        "children": [],
                    }
                    childrens.append(cur_level1)
                elif line.startswith("#### "):
                    content = line.strip().replace("#### ", "")
                    if cur_level1 is not None:
                        cur_level1["children"].append(
                            {
                                "node_type": "nt_span",
                                "text": content,
                                "level": 2,
                                "children": [],
                            }
                        )
                elif line.startswith("* "):
                    content = line.strip().replace("* ", "")
                    # Ensure cur_level2 is assigned before using
                    if cur_level1 is not None and cur_level1["children"]:
                        cur_level2 = cur_level1["children"][-1]
                        cur_level2["children"].append(
                            {
                                "node_type": "nt_span",
                                "text": content,
                                "level": 3,
                            }
                        )
        logger.info(f"章节内容: {id_childrens}")
        return id_childrens

    def generate_ppt_all(self, session_id):
        last_group_id = self.get_last_group_id(session_id)
        return self.generate_ppt(session_id, last_group_id)

    def theme_tpl(self):
        url = f"https://{self.host}/api/aigc/v3/assistant/ppt/theme_tpl"
        data = {
            "limit": 2,
            "offset": 0,
            "theme_filter": {},
            "theme_from": "aiTemplates",
        }
        response = self.request_sesion.post(url, json=data)
        logger.info(f"theme_tpl response: {response.text}")
        item = response.json().get("data", {}).get("items", [])[0]
        if not item:
            logger.error("No items found in theme_tpl response")
            return None, None
        return item["theme_id"], item["theme_key"]

    def generate_ppt(self, session_id, group_id):
        logger.info(
            f"Starting generate_ppt for session_id: {session_id}, group_id: {group_id}"
        )
        # create_card 1
        card_data_resp = self.create_card(session_id, group_id).json()
        message_id = card_data_resp.get("data", {}).get("message_id", "")

        # gen 1

        card_data = self.prepare_card_data(card_data_resp)
        pptx_params = {"slides_count": -1}
        card_data["pptx_params"] = pptx_params

        theme_id, theme_key = self.theme_tpl()
        card_data["theme_id"] = theme_id
        card_data["theme_key"] = theme_key
        logger.info(f"card_data {card_data}")
        # 深拷贝card_data
        card_data_copy = copy.deepcopy(card_data)
        for child in card_data["outlines"]["root_node"]["children"]:
            del child["id"]
        request_id, response_text = self.ppt_generate(
            session_id,
            card_data,
        )

        # gen 2
        request_id, response_text = self.ppt_body_generate(session_id, group_id)

        # gen 3
        chapters = self.parse_ppt_body(response_text)

        for child in card_data_copy["outlines"]["root_node"]["children"]:
            chapter_id = child.get("id", "")
            logger.info(f"child {child}")
            if not chapter_id:
                continue
            logger.info(f"chapter_id: {chapter_id}, {chapters.get(chapter_id, [])}")
            if chapter_id in chapters:
                child["children"] = chapters.get(chapter_id, [])
            else:
                child["children"] = []
            del child["id"]
        content = self.node_to_text(card_data_copy["outlines"]["root_node"])
        card_data_copy["content"] = content
        request_id, response_text = self.ppt_generate(
            session_id,
            card_data_copy,
        )
        logger.info(f"card_data_copy {card_data_copy}")

        # put card 1
        ppt_outline_structure = card_data_resp["data"]["card_data"][
            "ppt_outline_structure"
        ]
        slides = ppt_outline_structure.get("slide", [])
        for slide in slides:
            slide["titles"] = [{"value": slide["titles"][0]["value"]}]
            if "children" in slide:
                for child in slide["children"]:
                    del child["id"]

        outline_slide_map = []
        outline_slide_map2 = []
        for slide in slides:
            value = slide["titles"][0]["value"]
            if slide["type"] == "cover":
                outline_slide_map2.append(
                    {
                        "page_type": "pt_title",
                        "title_text": value,
                    }
                )
            elif slide["type"] == "outline":
                outline_slide_map2.append(
                    {
                        "page_type": "pt_contents",
                        "title_text": value,
                    }
                )
            elif slide["type"] == "chapter":
                outline_slide_map2.append(
                    {
                        "page_type": "pt_section_title",
                        "title_text": value,
                    }
                )
            elif slide["type"] == "content":
                outline_slide_map2.append(
                    {
                        "page_type": "pt_text",
                        "title_text": value,
                    }
                )
        for slide in outline_slide_map2:
            if slide["page_type"] != "pt_text":
                outline_slide_map.append(slide)

        card1 = {
            "outline": content,
            "outline_slide_map": outline_slide_map,
            "ppt_outline_structure": ppt_outline_structure,
            "theme_id": theme_id,
            "theme_key": theme_key,
        }
        self.put_create_card(session_id, message_id, card1)

        card1["outline_slide_map"] = outline_slide_map2
        self.put_create_card(session_id, message_id, card1)
        return card_data_copy

    def node_to_text(self, node, depth=0):
        text = node.get("text", "")
        if depth == 0:
            text = f"# {text}"
        elif depth == 1:
            text = f"## {text}"
        elif depth == 2:
            text = f"### {text}"
        elif depth == 3:
            text = f"#### {text}"
        elif depth == 4:
            text = f"* {text}"
        if "children" in node and node["children"]:
            for child in node["children"]:
                text += "\n\n" + self.node_to_text(child, depth + 1)
        return text.strip()

    def ppt_body_generate(self, session_id, group_id):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/ppt/body/generate"
        data = {"group_id": group_id}
        logger.info(f"Making request to URL: {url} with data: {data}")
        response = self.request_sesion.post(url, json=data)
        response.raise_for_status()
        response.encoding = "utf-8"
        # print(response.headers)
        # print(response.text)

        request_id = response.headers["x-request-id"]
        logger.info(
            f"PPT generation request completed successfully. Request ID: {request_id}"
        )
        logger.debug(f"Response text: {response.text}")
        return request_id, response.text

    def ppt_generate(
        self,
        session_id,
        card_data,
    ):
        logger.info(f"Starting generate_ppt for session_id: {session_id}")
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/ppt/generate"
        data = card_data
        logger.info(f"Making request to URL: {url} with data: {data}")
        response = self.request_sesion.post(url, json=data)
        response.raise_for_status()
        response.encoding = "utf-8"
        request_id = response.headers["x-request-id"]
        logger.info(
            f"/ppt/generate request completed successfully. Request ID: {request_id}"
        )
        logger.info(f"Response text: {response.text}")
        return request_id, response.text

    def put_create_card(self, session_id, message_id, card_data):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/creation_card/{message_id}"
        data = {"card_data": card_data}
        response = self.request_sesion.put(url, json=data)
        logger.info(
            f"PUT request to {url} with data: {data} returned {response.headers.get('x-request-id')}  {response.text}"
        )
        return response

    def create_card(self, session_id, group_id, empty_file=None):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/creation_card"
        if empty_file is None:
            data = {"group_id": group_id}
        else:
            data = {"group_id": group_id, "empty_file": empty_file}
        response = self.request_sesion.post(url, json=data)
        logger.info(f"create_card response: {response.text}")
        return response

    def save_docx(self, session_id, group_id):
        response = self.create_card(session_id, group_id, False)
        request_id = response.headers["x-request-id"]
        return (request_id, response.json())

    def generate_longwriter(self, session_id, group_id):
        self.create_card(session_id, group_id, True)
        last_group_id = self.get_last_group_id(session_id)
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/long_writer/{last_group_id}/body/generate"
        response = self.request_sesion.post(url, json={})
        response.raise_for_status()
        response.encoding = "utf-8"
        # print(response.headers)
        # print(response.text)
        request_id = response.headers["x-request-id"]
        return request_id, response.text

    def recommend_questions(self, file_id=None, file_name=None, kdc=None, content=None):
        url = f"https://{self.host}/api/aigc/v3/assistant/file/recommend"
        if file_id:
            data = {"file_id": file_id}
        elif content:
            data = {"file_name": file_name, "content": content}
        else:
            data = {"file_name": file_name, "kdc": kdc}
        logger.info(f"recommend_questions data: {data}")
        response = self.request_sesion.post(url, json=data)
        if response.status_code != 200:
            logger.error(
                f"Error in recommend_questions: {response.status_code} - {response.text}"
            )
        request_id = response.headers["x-request-id"]
        response.encoding = "utf-8"
        return request_id, response.json()


if __name__ == "__main__":
    cc = Copilot(is_test=False, wps_sid="")
    r = cc.questions(["你好"])
    print(r)

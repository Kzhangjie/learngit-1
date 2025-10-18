import requests
from dotenv import load_dotenv

load_dotenv()
import json
import os
import re
import time

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://lingxi.wps.cn/",
        "Origin": "https://lingxi.wps.cn",
        "Connection": "keep-alive",
        # 'X-Cc-Region': 'master',
        "Cookie": (
            f"wps_sid={wps_sid};wps_sid_prod={wps_sid};debug_api=1;search_engines={search_engines}"
            if is_test
            else f"wps_sid={wps_sid};debug_api=1"
        ),
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Priority": "u=1",
        "X-Cc-Version": "1",
        # 'x-client-type' : 'pc_web',
        "x-client-type": "mini_search",
        # 'Content-Length': '0',
        "X-Cc-Region": "lj2",
        # 'X-Cc-Region':'feat_copilot_cc_multi_agents'
        # 'X-Cc-Region':'feat_cc_switch_qvq_max'
        # 'X-Cc-Region':'master_old'
        # feat_copilot_r1  cc-lj
        # fix_deepseek_systemprompt  cc-lj
        # feat_copilot_cc_multi_agents
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

    def create_session(self):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions"
        response = self.request_sesion.post(url)
        res = response.json()
        print(url)
        print("Request Headers:", response.request.headers)
        print(response)
        print(res)
        if res.get("data") and res.get("data").get("session_id"):
            print("session_id", res["data"]["session_id"])
            return res["data"]["session_id"]
        else:
            print(f"创建session失败: {response.text}")
            return None

    def question(self, session_id, question):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/completions"
        # 文档引用文件信息处理
        file_ids = []
        before_canvas = ""
        canvas_fileid = ""
        command = False
        pattern = r"\[引用[^\]]*\]\(wps365://files/([^\)]+)\)"
        quote_files = re.findall(pattern, question)
        question = re.sub(pattern, "", question).strip()
        # 数据分析信息处理
        pattern2 = r"\[数据分析[^\]]*\]\(wps365://files/([^\)]+)\)"
        file_ids += re.findall(pattern2, question)
        if file_ids:
            command = True
        question = re.sub(pattern2, "", question).strip()
        # 上传文件信息处理
        pattern1 = r"\[[^\]]*\]\(wps365://files/([^\)]+)\)"
        file_ids += re.findall(pattern1, question)
        question = re.sub(pattern1, "", question).strip()

        pattern3 = r"\[(.*?)\]\(\*?(.*?)canvas\)\(wps365://files/(.*?)\)"
        match3 = re.search(pattern3, question)

        # 提取结果
        if match3:
            before_canvas = match3.group(2)  # 提取 canvas 前的内容
            canvas_fileid = match3.group(3)  # 提取 fileid
            print("==========================================")
            print("提取cavans", before_canvas)
            print("提取canvas的文件id", canvas_fileid)
            print("==========================================")

        # print ("之前的问题",question)
        question = re.sub(pattern3, "", question).strip()
        # print ("之后的问题",question)
        # 构造最终数据

        data = {"question": question}
        if before_canvas and canvas_fileid:
            if "context" not in data:
                data["context"] = {}  # 先初始化 context
            data["context"]["agent"] = before_canvas
            data["context"]["file_id"] = {"id": canvas_fileid, "type": "file"}
            # data["context"]["agent"] = before_canvas
            # data["context"]["file_id"]["id"] = canvas_fileid
            # data["context"]["file_id"]["type"] = "file"
        if quote_files:
            data["quote_files"] = quote_files
        if file_ids:
            data["file_ids"] = file_ids
        if command:
            data["command"] = "data_analysis"
        data["command"] = "mini_search"
        # data["command_args"] = {"length": "","disable_websearch": False}
        # length: "medium"
        # length: "short"
        # {length: "long"
        # print ("data")
        # data["reasoning"] = True

        # reasoning: true
        try:
            response = self.request_sesion.post(url, json=data)
            response.raise_for_status()
            response.encoding = "utf-8"
            print(response.text)
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

    def history(self, session_id):
        url = (
            f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/messages"
        )
        history_data = self.request_sesion.get(url).json()
        new_history = {
            "data": {"list": [entry for entry in history_data["data"]["list"]]},
            "result": history_data["result"],
        }
        return new_history

    def get_last_group_id(self, session_id):
        history = self.history(session_id)
        return history.get("data").get("list")[-1]["group_id"]

    def questions(self, questions):
        print(questions)
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
            r = self.question(session_id, q)
            rs.append(r)
        return (
            self.history(session_id),
            json.dumps(rs, ensure_ascii=False, indent=4),
            session_id,
        )

    def generate_ppt(self, session_id, group_id):
        self._create_card(session_id, group_id, False)
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/ppt/body/generate"
        data = {"group_id": group_id}
        response = self.request_sesion.post(url, json=data)
        response.raise_for_status()
        response.encoding = "utf-8"
        # print(response.headers)
        # print(response.text)
        request_id = response.headers["x-request-id"]
        return request_id, response.text

    def _create_card(self, session_id, group_id, empty_file):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/creation_card"
        data = {"group_id": group_id, "empty_file": empty_file}
        response = self.request_sesion.post(url, json=data)
        return response

    def save_docx(self, session_id, group_id):
        response = self._create_card(session_id, group_id, False)
        request_id = response.headers["x-request-id"]
        return (request_id, response.json())

    def generate_longwriter(self, session_id, group_id):
        self._create_card(session_id, group_id, True)
        last_group_id = self.get_last_group_id(session_id)
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/long_writer/{last_group_id}/body/generate"
        response = self.request_sesion.post(url, json={})
        response.raise_for_status()
        response.encoding = "utf-8"
        # print(response.headers)
        # print(response.text)
        request_id = response.headers["x-request-id"]
        return request_id, response.text

    def canvas_recommend(self, filename, fileid, filetype):
        url = f"https://{self.host}/api/aigc/v3/assistant/sessions/recommend"
        data = {"filename": filename, "type": filetype}
        response = self.request_sesion.post(url, json=data)
        responsestr = json.loads(response.text)
        qusetions = responsestr["data"]
        return json.dumps(qusetions, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    cc = Copilot(
        is_test=False,
    )
    # _, _, session_id = cc.questions(
    #     [
    #         "根据以下主题生成PPT：长夜余火",
    #     ]
    # )
    # last_group_id = cc.get_last_group_id(session_id)
    r = cc.generate_ppt("8658426108510408", "8658426123845657")
    print(r)

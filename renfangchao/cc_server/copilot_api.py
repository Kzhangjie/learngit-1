import json
import os
import warnings
from dataclasses import dataclass
from datetime import datetime

import requests
import urllib3

# Disable InsecureRequestWarning warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
import sseclient


class CopilotBase:
    def __init__(
        self, is_test=False, model_url="", custom_headers={}, search_engines=""
    ):
        self.is_test = is_test
        self.model_url = model_url
        self.custom_headers = custom_headers
        self.search_engines = search_engines
        self.wps_sid = (
            os.environ["WPS_SID_TEST"] if self.is_test else os.environ["WPS_SID"]
        )
        self.headers = self.get_headers()
        self.host = "120.92.124.158" if self.is_test else "lingxi.wps.cn"
        self.prefix = f"https://{self.host}"

    def get_headers(self):
        """Set headers dynamically based on the environment."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://lingxi.wps.cn/",
            "Origin": "https://lingxi.wps.cn",
            "Connection": "keep-alive",
            "Cookie": (
                f"wps_sid={self.wps_sid};wps_sid_prod={self.wps_sid};debug_api=1;search_engines={self.search_engines}"
                if self.is_test
                else f"wps_sid={self.wps_sid};debug_api=1"
            ),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "Priority": "u=1",
        }
        if self.is_test:
            headers["Host"] = "lingxi.wps.cn"
        if self.model_url:
            headers["Cookie"] += f";model_url={self.model_url}"
        headers.update(self.custom_headers)
        return headers

    def make_request(
        self,
        endpoint,
        method="GET",
        data=None,
        params=None,
        timeout=10,
        return_json=True,
    ):
        """Generalized method to send requests."""
        url = f"{self.prefix}/{endpoint}"
        try:
            print(
                f"Making {method} request to {url} with data: {data} ,params:{params}"
            )  # Log request
            if method.upper() == "GET":
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    verify=False,
                    timeout=timeout,
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    verify=False,
                    timeout=timeout,
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    verify=False,
                    timeout=timeout,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.encoding = "utf-8"
            response.raise_for_status()
            # print(
            #     f"Response status: {response.status_code}, Response: {response.text}"
            # )  # Log response
            print(f"Response status: {response.status_code}")
            if return_json:
                return response.json()
            else:
                return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None


@dataclass
class ComplectionEvent:
    event: str
    data: dict

    def to_dict(self):
        return {"event": self.event, "data": self.data}

    def __json__(self):
        return {"event": self.event, "data": self.data}


from typing import Any, Dict, List


class Copilot(CopilotBase):
    def __init__(
        self, is_test=False, model_url="", custom_headers={}, search_engines=""
    ):
        super().__init__(is_test, model_url, custom_headers, search_engines)
        self.prefix = f"{self.prefix}/api/aigc/v3/assistant"

    def get_admin_instance(self):
        """从当前 Copilot 实例生成一个 CopilotAdmin 实例"""
        return CopilotAdmin(
            is_test=self.is_test,
            model_url=self.model_url,
            custom_headers=self.custom_headers,
            search_engines=self.search_engines,
        )

    def create_session(self):
        """Create a new session and return the session ID."""
        response = self.make_request("sessions", method="POST")
        if response and "data" in response and "session_id" in response["data"]:
            return response["data"]["session_id"]
        else:
            print(f"Failed to create session: {response}")
            return None

    def completions(
        self,
        session_id,
        question,
        file_ids=[],
        reference_search_id="",
        command="",
        group_id="",
        command_args={},
        collect_ids=[],
    ) -> tuple[List[ComplectionEvent], str]:
        """Ask a question in an existing session."""
        data = {
            "question": question,
            "file_ids": file_ids,
            "reference_search_id": reference_search_id,
            "command": command,
            "group_id": group_id,
            "command_args": command_args,
            "collect_ids": collect_ids,
        }
        response = self.make_request(
            f"sessions/{session_id}/completions",
            method="POST",
            data=data,
            return_json=False,
        )
        if response:
            request_id = response.headers["x-request-id"]
        else:
            print("Failed to get a valid response.")
            return [], ""
        stream = sseclient.SSEClient(response)
        events = []
        for event in stream.events():
            e = ComplectionEvent(
                event.event, json.loads(event.data) if event.data else {}
            )
            events.append(e)
        return events, request_id

    def questions(self, questions):
        """Ask multiple questions in a single session."""
        session_id = self.create_session()
        if not session_id:
            return None, None

        responses = []
        for q in questions:
            if isinstance(q, str):
                response = self.completions(session_id, q)
            else:
                response = self.completions(session_id, **q)
            responses.append(response)

        return session_id, responses

    def question(self, question, file_ids=[], reference_search_id="", command=""):
        session_id = self.create_session()
        if not session_id:
            return None, None
        response = self.completions(
            session_id,
            question,
            file_ids,
            reference_search_id=reference_search_id,
            command=command,
        )
        return session_id, response

    def delete_session(self, session_id):
        """Delete a session."""
        return self.make_request(f"sessions/{session_id}", method="DELETE")

    def rename_session(self, session_id, new_title):
        """Rename a session."""
        data = {"title": new_title}
        return self.make_request(
            f"sessions/{session_id}/rename", method="POST", data=data
        )

    def post_comment(self, session_id, message_id, comment_status="up", comment=""):
        """
        点赞或点踩，踩的时候可以添加评论。赞和踩状态只能有一个，不能同时存在。
        Parameters:
        - session_id: ID of the session.
        - message_id: ID of the message.
        - comment_status: Status of the comment, either 'up' or 'down'. Default is 'up'.
        - comment: The comment text. Default is ''.
        """
        data = {"comment_status": comment_status}
        if comment:
            data["comment"] = comment
        return self.make_request(
            f"sessions/{session_id}/messages/{message_id}/comment",
            method="POST",
            data=data,
        )

    def delete_comment(self, session_id, message_id):
        """Delete a comment on a message."""
        return self.make_request(
            f"sessions/{session_id}/messages/{message_id}/comment", method="DELETE"
        )

    def query_session_list(self, offset=0, limit=30, start_time=None, end_time=None):
        """Query the list of sessions."""
        params = {
            "offset": offset,
            "limit": limit,
            "start_time": start_time,
            "end_time": end_time,
        }
        return self.make_request("sessions", method="GET", params=params)

    def messages(self, session_id, offset=0, limit=100, order_by="asc"):
        """Query the chat messages in a session."""
        params = {"offset": offset, "limit": limit, "order_by": order_by}
        return self.make_request(
            f"sessions/{session_id}/messages", method="GET", params=params
        )

    def get_messages(self, session_id, offset=0, limit=100, order_by="asc"):
        data = self.messages(session_id, offset, limit, order_by)
        return data["data"]["list"]

    # def polish_message(self, session_id, group_id, action):
    #     """废弃 Polish a message."""
    #     data = {"action": action}
    #     return self.make_request(f"sessions/{session_id}/messages/{group_id}/polish", method="POST", data=data)

    def modify_ppt_outline(
        self, session_id, message_id, node_root, content, doc_type="ppt"
    ):
        """界面手动编辑大纲"""
        data = {"message_id": message_id, "root_node": node_root, "content": content}
        return self.make_request(
            f"sessions/{session_id}/save/{doc_type}/outline", method="POST", data=data
        )

    # def ask_recommendation(self, session_id, user_text, assistant_text):
    #     """废弃 Generate recommended questions."""
    #     data = {"user": user_text, "assistant": assistant_text}
    #     return self.make_request(f"sessions/{session_id}/text/recommend", method="POST", data=data)

    def report_message(self, session_id, message_id, label, input_text, output_text):
        """举报"""
        data = {"label": label, "input": input_text, "output": output_text}
        return self.make_request(
            f"sessions/{session_id}/messages/{message_id}/report",
            method="POST",
            data=data,
        )

    def save_to_file(
        self, session_id, message_id, node_root, content, doc_type="ppt", group_id=""
    ):
        """界面点"保存PPT",保存PPT到文件"""
        data = {
            "message_id": message_id,
            "root_node": node_root,
            "type": doc_type,
            "group_id": group_id,
            "content": content,
        }
        response = self.make_request(
            f"sessions/{session_id}/save/files",
            method="POST",
            data=data,
            return_json=False,
        )
        stream = sseclient.SSEClient(response)
        events = []
        for event in stream.events():
            e = ComplectionEvent(event.event, json.loads(event.data))
            events.append(e)
        return events


class CopilotAdmin(CopilotBase):
    def __init__(
        self, is_test=False, model_url="", custom_headers={}, search_engines=""
    ):
        super().__init__(is_test, model_url, custom_headers, search_engines)
        self.prefix = f"{self.prefix}/api/aigc/admin"

    # API methods for Admin
    def get_session_list(
        self,
        company_id="",
        offset=0,
        limit=30,
        start_time=0,
        end_time=None,
        creator_id="",
        exclude_uids="",
        exclude_company_ids="",
        user_type="",
        order="asc",
        title="",
    ):
        """获取会话列表"""
        if not end_time:
            end_time = int(datetime.now().timestamp())
        params = {
            "company_id": company_id,
            "offset": offset,
            "limit": limit,
            "start_time": start_time,
            "end_time": end_time,
            "creator_id": creator_id,
            "exclude_uids": exclude_uids,
            "exclude_company_ids": exclude_company_ids,
            "user_type": user_type,
            "order": order,
            "title": title,
        }
        return self.make_request("sessions", method="GET", params=params)

    def get_chat_messages(
        self, session_id, offset=0, limit=30, message_type="outside", typ=""
    ):
        """获取会话中的消息"""
        params = {
            "offset": offset,
            "limit": limit,
            "message_type": message_type,
            "type": typ,
        }
        return self.make_request(
            f"sessions/{session_id}/messages", method="GET", params=params
        )

    def get_chat_prompt(self, session_id, event="", chat_id=""):
        """获取会话的Prompt"""
        params = {"event": event, "chat_id": chat_id}
        return self.make_request(
            f"sessions/{session_id}/prompt", method="GET", params=params
        )

    def get_user_messages(self, session_id, user_id, message_ids=[], group_ids=[]):
        """获取用户消息"""
        params = {
            "user_id": user_id,
            "message_ids": message_ids,
            "group_ids": group_ids,
        }
        return self.make_request(
            f"sessions/{session_id}/user_messages", method="GET", params=params
        )

    def get_code(self, session_id):
        """获取代码信息"""
        return self.make_request(f"sessions/{session_id}/code", method="GET")

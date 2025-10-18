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


def get_headers(is_test, model_url, search_engines):
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
        # 'Content-Length': '0',
        # 'X-Cc-Region':'image'
        "X-Cc-Region": "feat_cc_deepseekv3_api",  # 分支名
        # feat_copilot_r1
        # fix_deepseek_systemprompt  cc-lj
    }
    if is_test:
        headers["Host"] = "lingxi.wps.cn"
    if model_url:
        headers["Cookie"] = headers["Cookie"] + f";model_url={model_url}"
    print(111, headers)
    print(111, WPS_SID_TEST)
    return headers


class Copilot:
    def __init__(
        self, is_test=True, model_url="", custom_headers={}, search_engines=""
    ):
        self.is_test = is_test
        self.model_url = model_url
        self.request_sesion = requests.Session()
        self.session_id = None
        self.headers = get_headers(is_test, model_url, search_engines)
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

        # 构造最终数据
        data = {"question": question}
        if quote_files:
            data["quote_files"] = quote_files
        if file_ids:
            data["file_ids"] = file_ids
        if command:
            data["command"] = "data_analysis"  # 对应前端的数据分析勾选
        # data["command"] = "generateppt"  # ppt的，暂时注释
        # data["command_args"] = {"length": "short","disable_websearch": True}
        # length: "medium"
        # length: "short"
        # {length: "long"
        # print ("data")
        data["reasoning"] = True  # 控制走R1

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


if __name__ == "__main__":
    cc = Copilot(
        is_test=True,
        model_url="http://10.8.254.24:30818/kas/vbzjnuaoydcextkitrv9vj7yfrkv/api/chat/completions?model=0808-llmf",
    )
    r = cc.questions(["搜下范特西", "clLTLnUPuCCO"])
    print(r)

import io

import requests
from dotenv import load_dotenv

load_dotenv()
import json
import os
import time

from utils import getLogger

logger = getLogger(os.path.splitext(os.path.basename(__file__))[0])
WPS_SID = os.environ["WPS_SID"]
WPS_SID_TEST = os.environ["WPS_TEST_SID"]
WPS_SID_TEST = WPS_SID
import urllib3

# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
scheme = "http"
import sseclient


def get_test_url(url):
    return url.replace("copilot.wps.cn", "120.92.124.158")


MM = "model-3p"
豆包 = "model-s"
GLM = "model-y"

模型 = 豆包
model = f"model={模型};"


# model = ""
def get_headers(is_test, model_url):
    wps_sid = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://copilot.wps.cn/",
        "Origin": "https://copilot.wps.cn",
        "Connection": "keep-alive",
        "Cookie": (
            f"{model}wps_sid={wps_sid};wps_sid_prod={wps_sid};debug_api=1"
            if is_test
            else f"{model}wps_sid={wps_sid};debug_api=1;model=model-s"
        ),
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Priority": "u=1",
        # 'Content-Length': '0',
        # 'x-cc-branch':'wgr'
    }
    if is_test:
        headers["Host"] = "copilot.wps.cn"
    if model_url:
        headers["Cookie"] = headers["Cookie"] + f";model_url={model_url}"
    # print(111,headers)
    return headers


def log_request_response(d):
    request_info = f"""-------------- 请求开始 --------------
URL: {d['request']['url']}
Headers: {d['request']['headers']}
Body: {d['request']['body']}
-------------- 响应开始 --------------
Status Code: {d['response']['status_code']}
Headers: {d['response']['headers']}
Body: {d['response']['body']}
-------------- 响应结束 ----------------"""

    print(request_info)


class Copilot:
    def __init__(self, is_test=True, model_url="", custom_headers={}):
        self.is_test = is_test
        self.model_url = model_url
        self.request_sesion = requests.Session()
        self.session_id = None
        self.headers = get_headers(is_test, model_url)
        self.request_sesion.headers.update(self.headers)
        self.request_sesion.headers.update(custom_headers)
        self.request_sesion.verify = False
        self.host = "120.92.124.158" if self.is_test else "copilot.wps.cn"

    def create_session(self):
        url = f"{scheme}://{self.host}/api/aigc/v3/assistant/sessions"
        response = self.request_sesion.post(url)
        res = response.json()
        if res.get("data") and res.get("data").get("session_id"):
            return res["data"]["session_id"]
        else:
            print(f"创建session失败: {response.text}")
            return None

    def question(self, session_id, question):
        url = f"{scheme}://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/completions"
        data = {"question": question, "file_ids": ["cf6AyWztRskY"]}
        try:
            response = self.request_sesion.post(url, json=data)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

    def history(self, session_id):
        url = f"{scheme}://{self.host}/api/aigc/v3/assistant/sessions/{session_id}/messages"
        print("============================")
        print(url)
        print("============================")
        print(f"Headers being sent: {self.request_sesion.headers}")
        return self.request_sesion.get(url).json()

    def questions(self, questions):
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
        for i, q in enumerate(questions):
            r = self.question(session_id, q)
            print(r)
            # if i == 2:
            #     if "智能" in r:
            #         print("bug----------")
            #         print(r)
            #     else:
            #         print("ok")

            # time.sleep(2)
            # for s in r.split("\n"):
            #     if s.startswith("""data:{"type": "text", "data": "网关"""):
            #         s = s[5:]
            #         print(1111,s)
            #         s = json.loads(s)
            #         payload = s["data"][2:]
            #         rs.append(payload)
            #         print("prompt",payload)
            # rs.append(r)
            byte_stream = io.BytesIO(r.encode("utf-8"))

            stream = sseclient.SSEClient(byte_stream)
            for event in stream.events():
                # print(event)
                if event.event == "req":
                    data = json.loads(event.data)
                    for d in data:
                        log_request_response(d)
        return rs, session_id
        # return self.history(session_id),json.dumps(rs,ensure_ascii=False,indent=4),session_id


if __name__ == "__main__":
    cc = Copilot(
        is_test=True,
        model_url="http://kmd-api.kas.wps.cn/api/10783/BJfiZy/api/chat/completions",
    )
    cc.host = "127.0.0.1:5000"
    # r = cc.create_session()
    for i in range(1):
        cc.questions(["内容是什么？"])
        # cc.questions(["帮我写首关于北方的诗","写的不好","sb"])
    # print(11111)
    # print(h)
    # print(p)
    # print(id)

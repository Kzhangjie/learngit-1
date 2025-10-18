import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from tqdm import tqdm

import airsheet
from run_batch.run_base import RunBase
from utils.gateway_api_v2_stream import GateWayAPI


class websearch:
    def __init__(self, wps_sid: str = None, token: str = None): # type: ignore\
        self.__headers = {
            "AI-Gateway-Uid": "1388383710",
            "Cookie": f"wps_sid={wps_sid}",
            "Authorization": f"Bearer {token}",
        }

    def __call__(self, query: str):
        body = {
            "query": query,
        }
        # print(self.__headers)
        resp = requests.post(
            "https://copilot.wps.cn/api/aigc/v3/dev/websearch",
            json=body,
            headers=self.__headers,
        )
        print(resp.text)
        res = resp.json()
        return res["data"]["references"]
    

wso = websearch("")
        
if __name__ == "__main__":
    print(111)
    ws = websearch("")
    res = ws("鲁迅")
    print(res)    res = ws("鲁迅")
    print(res)
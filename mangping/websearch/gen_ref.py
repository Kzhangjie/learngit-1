from types import MethodType

from run_batch.run_ai import RunAi

file_id = "cj5JoUT6yarM"
sheetname = "搜索"
必须有的列名 = ["问题"]
输出列名 = "search_1"
输出列编号 = "L"

import airsheet

sp = """"""
print(2)

from utils.gateway_api_v2_stream import GateWayAPI

api = GateWayAPI(retry_count=10)

import requests

from mangping.mangping_utils import chat_retry, r2q


class websearch:
    def __init__(self, wps_sid: str = None, token: str = None):  # type: ignore\
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


wso = websearch(
    "",
    "960bf484c4a3d26ec6fcb23923b7785c",
)
import json


def run_one(self, row):
    key_str = row["code"].strip()
    # 去掉开头的 '<|FunctionCallBegin|>'
    key_str = key_str.replace("<|FunctionCallBegin|>", "")
    keys = json.loads(key_str)
    query = keys.get("args", {}).get("query", "")
    p = keys.get("args", {}).get("prompt", "")
    results = wso(query)
    model_message = json.dumps(results, ensure_ascii=False)
    m1 = model_message[:30000]
    m2 = model_message[30000:60000]
    m3 = model_message[60000:90000]
    m4 = model_message[90000:120000]
    data = [m1, m2, m3, m4]
    airsheet.write_xl(
        data,
        f'{输出列编号}{row["row_index"]}',
        sheet_name=self.sheetname,
    )


if __name__ == "__main__":
    ss = [sheetname]

    for s in ss:
        ai = RunAi(
            file_id=file_id,
            sheetname=s,
            must_have_columns=必须有的列名,
            skip_col_name=输出列名,
            clo_num_to_write=输出列编号,
            max_workers=10,
        )
        ai.run_one = MethodType(run_one, ai)
        ai.run()
        ai.run()

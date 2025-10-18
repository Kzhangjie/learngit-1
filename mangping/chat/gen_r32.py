from types import MethodType
from run_batch.run_ai import RunAi

file_id = "cc8qH3Onudyw"
sheetname = "闲聊"
sheetname = "创作"
必须有的列名 = ["问题"]
输出列名 = "C_reason_1"
输出列编号 = "I"
输出列名前缀 = "C_answer_"
import airsheet
import traceback
import json

from mangping.chat.chat_prompts import system_prompt

sp = system_prompt()


import requests


# 设置请求头
headers = {"Content-Type": "application/json"}

# 设置请求体

import re


def chat(msg):
    for m in msg:
        m["type"] = "text"
    body = {
        "model": "dpsk32",
        "stop": ["<|endofblock|>", "<|endofmessage|>"],
        "stream": False,
        "temperature": 0.6,
        "messages": msg,
    }
    resp = requests.post(
        "http://120.92.122.107:30818/kas/dqk2ckuumnugdylwla8hxk12zvvo/v1/chat/completions?model=dpsk32",
        json=body,
        headers=headers,
    )
    # print(resp.text)
    resp = resp.json()

    content = resp["choices"][0]["message"]["content"]

    pattern = r"<think>(.*?)</think>(.*)"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        part1 = match.group(1).strip()
        part2 = match.group(2).strip()
        return part2, part1
    else:
        return content, ""


from mangping.mangping_utils import chat_retry, r2q


def run_one(self, row):

    q = r2q(row)
    history = [
        {
            "role": "system",
            "content": sp,
        },
        {
            "role": "user",
            "content": q,
        },
    ]
    content, resson_content = chat_retry(history, chat)
    data = [resson_content, content]
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
            max_workers=5,
        )
        ai.run_one = MethodType(run_one, ai)
        ai.run()

from types import MethodType
from run_batch.run_ai import RunAi

file_id = "cc8qH3Onudyw"
sheetname = "盲评记录"
必须有的列名 = ["问题"]
输出列名 = "ai_reason"
输出列编号 = "S"

import airsheet


from utils.gateway_api_v2_stream import GateWayAPI

api = GateWayAPI(retry_count=10)

from mangping.mangping_utils import chat_retry, r2q
from mangping.readfile.prompts import row_to_documents
import random


def row_to_prompt(row, change):
    q = r2q(row)
    documents = row_to_documents(row)

    a, b = [row["答案A"], row["答案B"]]
    if change:
        a, b = b, a

    return f"""请作为裁判，公正的评判哪个AI的回答对用户给有用。
# 用户的问题
{q}

# 用户提供的文档
[documents_content_begin]
{documents}
[documents_content_end]

# A的回答
[answer_A_begin]
{a}
[answer_A_end]

# B的回答

[answer_B_begin]
{b}
[answer_B_end]

# 输出格式

我的判断是：[你的理由]

最有用的回答是：[[A]] 或 [[B]] 或 [[平局]]。
"""


import re


def extract_answer(text):
    match = re.search(r"\[\[(A|B|平局)\]\]", text)
    if match:
        return match.group(1)
    return None


def run_one(self, row):
    random.seed(row["row_index"])
    change = random.choice([True, False])
    prompt = row_to_prompt(row, change)
    success, text, others = api.chat_text(
        "deepseek-reasoner-ark",
        prompt,
        context="",
        llm_arguments={"temperature": 0.6},
    )
    result = extract_answer(text)
    if change:
        if result == "A":
            result = "B"
        elif result == "B":
            result = "A"
    if result != "平局":
        result = f"答案{result}"
    data = [others.get("reasoning_content", ""), text, result, change]
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
            max_workers=6,
        )
        ai.run_one = MethodType(run_one, ai)
        ai.run()

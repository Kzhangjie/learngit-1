from types import MethodType
from run_batch.run_ai import RunAi

file_id = "cj5JoUT6yarM"
sheetname = "创作"
sheetname = "闲聊"
必须有的列名 = ["问题"]
输出列名 = "qwen_reason"
输出列编号 = "P"

import airsheet

from mangping.readfile.prompts import system_prompt, row_to_prompt

sp = ""


from utils.gateway_api_v2_stream import GateWayAPI

api = GateWayAPI(retry_count=10)

from mangping.mangping_utils import chat_retry, r2q
from mangping.qwen_api import chat_text


def run_one(self, row):
    success, text, others = chat_text(r2q(row), context=sp)

    data = [others.get("reasoning_content", ""), text]
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

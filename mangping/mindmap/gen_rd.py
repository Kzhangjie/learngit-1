from types import MethodType
from run_batch.run_ai import RunAi

file_id = "cj5JoUT6yarM"
sheetname = "脑图"
必须有的列名 = ["问题"]
输出列名 = "dpsk32_reason"
输出列编号 = "I"

import airsheet

from mangping.mindmap.prompts import system_prompt, row_to_prompt

sp = ""


from utils.gateway_api_v2_stream import GateWayAPI
from mangping.doubao_think import chat_text

# api = GateWayAPI(retry_count=10)

from mangping.mangping_utils import chat_retry, r2q


def run_one(self, row):
    prompt = row_to_prompt(row)
    success, text, others = chat_text(prompt, context=sp)

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
            max_workers=10,
        )
        ai.run_one = MethodType(run_one, ai)
        ai.run()

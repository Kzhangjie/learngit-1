from types import MethodType
from run_batch.run_ai import RunAi

file_id = "cj5JoUT6yarM"
sheetname = "长文写作"
必须有的列名 = ["问题"]
输出列名 = "r1_reason"
输出列编号 = "G"

import airsheet

from mangping.longwrite.prompts import system_prompt, row_to_prompt

sp = ""


from utils.gateway_api_v2_stream import GateWayAPI

api = GateWayAPI(retry_count=10)

from mangping.mangping_utils import chat_retry, r2q


def run_one(self, row):
    prompt = row_to_prompt(row)
    success, text, others = api.chat_text(
        "deepseek-reasoner-ark", prompt, context=sp, llm_arguments={"temperature": 0.6}
    )

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

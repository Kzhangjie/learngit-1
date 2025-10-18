from types import MethodType
from run_batch.run_ai import RunAi


file_id = "chUgXk8Wzg6k"
sheetname = "URL解析"
必须有的列名 = ["问题"]
输出列名 = "doubao_answer"
输出列编号 = "F"

import airsheet


from mangping.readurl.prompts import system_prompt, row_to_prompt

sp = system_prompt("doubao")


from utils.gateway_api_v2_stream import GateWayAPI

api = GateWayAPI(retry_count=10)


def run_one(self, row):
    prompt = row_to_prompt(row)
    success, text, _ = api.chat_text("Doubao-1.5-pro-256k", prompt, context=sp)
    data = [text]
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

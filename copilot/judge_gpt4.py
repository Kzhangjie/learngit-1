import datetime
from types import MethodType
from run_batch.run_ai import RunAi
import re


import re
from run_batch.code_utils.validate_json_in_text import extract_json_from_text



file_id = "ckIo5P74CaXT"
sheetname = "websearch_rfc" 

必须有的列名 = ["WPS答案可视化"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "GPT测试详情" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "X" # 表示从把答案写到C列
模型 = "gpt-4"
模型参数 ={
    "temperature":0.0
}
from utils.gateway_api_v2_stream import GateWayAPI
import airsheet
import traceback
api = GateWayAPI()
from gen_prompt import gen_prompt
from datetime import datetime

context = f"当前时间是{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
import json
def run_one(self,row):
    max_retry = 5
    try:
        for i in range(max_retry):
            p = gen_prompt(row)
            # print(p)
            # break
            success,result,response = api.chat_text(model=模型,text=p,context=context,llm_arguments=模型参数,version="0125-Preview")
            if success:
                break
        airsheet.write_xl([result], f'{输出列编号}{row["row_index"]}', sheet_name=self.sheetname)
    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    ai = RunAi(file_id=file_id,sheetname=sheetname,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=8)
    ai.run_one = MethodType(run_one, ai)
    ai.run()
#     raw_string = """
# 准确答案:圣马太蒙召 或 圣马太的召唤
# 参考答案:通常不打草稿
# 准确答案:这是一个包含换行符的答案
# 换行部分
# """
#     a = parse_answer(raw_string)
#     print(a)
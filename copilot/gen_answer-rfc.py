from types import MethodType
from run_batch.run_ai import RunAi


file_id = "chMCLGCfF4Ih"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
必须有的列名 = ["问题"] 
输出列名 = "WPS答案"
输出列编号 = "P"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api2 import Copilot
cc = Copilot(is_test=True,model_url="",custom_headers={})
def run_one(self,row):
    try:
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        answer,logs = cc.questions(qs)
        result = json.dumps(answer,ensure_ascii=False,indent=4)
        r1 = result[:30000]
        r2 = result[30000:]
        text = convert_messages_for_gpt(answer)
        # text = ''
        codes = extra_codes(answer)
        # codes = ''
        airsheet.write_xl([r1,r2,logs,text,codes], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    ss = [sheetname3]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=1)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
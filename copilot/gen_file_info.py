from types import MethodType
from run_batch.run_code import RunCode


file_id = "cluD9scAA7BG"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
必须有的列名 = ["WPS答案"] 
输出列名 = "文件内容"
输出列编号 = "AO"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from api2 import Copilot
from file_info_api import get_message_file

def run_one(self,row):
    try:
        answer = json.loads(row["WPS答案"]+row.get("WPS答案1","")+row.get("WPS答案2","")+row.get("WPS答案3",""))
        file_info = get_message_file(answer)
        file_info_json = json.dumps(file_info,ensure_ascii=False,indent=4)
        f1 = file_info_json[:30000]
        f2 = file_info_json[30000:60000]
        f3 = file_info_json[60000:90000]
        f4 = file_info_json[90000:120000]
        return [f1,f2,f3,f4]
    except Exception as e:
        print(traceback.format_exception(e))
        return ["","",""]

if __name__ == '__main__':
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4]
    ss = [sheetname1]
    for s in ss:
        ai = RunCode(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
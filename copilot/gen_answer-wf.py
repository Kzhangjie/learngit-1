from types import MethodType
from run_batch.run_ai import RunAi


file_id = "crU6mjHEw8VJ"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
sheetname5 = "人设_验证集"
sheetname6 = "引用文档 (2)"
# sheetname = "豆包"
# sheetname6 = "tencent,doubao"


必须有的列名 = ["问题"] 
输出列名 = "WPS答案"
输出列编号 = "O"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages
from api2 import Copilot
cc = Copilot(is_test=True,model_url="http://10.8.254.24:30818/kas/ozqa77bfcq3iud6s1sjqhyhw6rcf/api/chat/completions?model=latest",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={},search_engines="")
def run_one(self,row):
    
    try:
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        # print (qs)
        answer,logs,s_id = cc.questions(qs)
        result = json.dumps(answer,ensure_ascii=False,indent=4)
        r1 = result[:30000]
        r2 = result[30000:60000]
        r3 = result[60000:90000]
        r4 = result[90000:120000]
        # log1 = logs[:30000]
        # log2 = logs[30000:60000]
        # log3 = logs[60000:90000]
        # log4 = logs[90000:120000]
        # text = convert_messages_for_gpt(answer)
        text = {
            "data": {
                "list": trans_chat_messages_2_messages(answer.get("data", {}).get("list", []), qs)
            },
            "result": answer.get("result")
        }
        # logs1 = json.dumps(text, ensure_ascii=False, indent=2)
        # log1 = logs1[:30000]
        # log2 = logs1[30000:60000]
        # log3 = logs1[60000:90000]
        # log4 = logs1[90000:120000]
        log1 = ""
        log2 = ""
        log3 = ""
        log4 = ""
        new_text = json.dumps(text, ensure_ascii=False, indent=2)
        codes = extra_codes(answer)
        # codes = ''
        codes_in_logs = extra_codes_from_logs(json.loads(logs))
        # codes_in_logs = ''
        airsheet.write_xl([f'\'{s_id}',r1,r2,r3,r4,log1,log2,log3,log4,new_text,codes,codes_in_logs], f'O{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([f'\'{s_id}',r1,r2,r3,r4,log1,log2,log3,log4,new_text,codes,codes_in_logs], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([codes_in_logs], f'AH{row["row_index"]}', sheet_name=self.sheetname)
    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    # ss = [sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname]
    ss = [sheetname6]
    # ss = [sheetname5]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=10)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
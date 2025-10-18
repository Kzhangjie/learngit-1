from types import MethodType
from run_batch.run_ai import RunAi


file_id = "ctsACceAf15p"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"

必须有的列名 = ["session_id"] 
输出列名 = "WPS答案"
输出列编号 = "P"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages
from api2 import Copilot
cc = Copilot(is_test=True,model_url="http://10.8.254.24:30818/kas/vbzjnuaoydcextkitrv9vj7yfrkv/api/chat/completions?model=0822_v1",custom_headers={},search_engines="")
def run_one(self,row):
    
    try:
        s_id = row["session_id"]
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        print (s_id)
        answer = cc.history(s_id)
        result = json.dumps(answer,ensure_ascii=False,indent=4)
        r1 = result[:30000]
        r2 = result[30000:60000]
        r3 = result[60000:90000]
        r4 = result[90000:120000]
        # text = convert_messages_for_gpt(answer)
        text = {
            "data": {
                "list": trans_chat_messages_2_messages(answer.get("data", {}).get("list", []), qs)
            },
            "result": answer.get("result")
        }
        
        new_text = json.dumps(text, ensure_ascii=False, indent=2)
        # codes = extra_codes(answer)
        codes = ''
        airsheet.write_xl([r1,r2,r3,r4], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        airsheet.write_xl([new_text], f'X{row["row_index"]}', sheet_name=self.sheetname)
    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4]
    ss = [sheetname4]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=4)
        ai.run_one = MethodType(run_one, ai)
        ai.run(1)
from types import MethodType
from run_batch.run_ai import RunAi


file_id = "chdnOzKQZm9Y"
sheetname = "Sheet1"
必须有的列名 = ["问题"] 
输出列名 = "拆词"
输出列编号 = "B"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api2 import Copilot
from code_session import chat_stream
model_url = "http://120.92.122.107:30818/kas/ybsjuqhgzi9-qkatvhtcdydnav5x/api/chat/completions?model=latest"
def run_one(self,row):
    try:
        que = row.get("问题","")
        messages = [
          {
            "role": "system",
            "type": "text",
            "content": "今天是:2025-04-01。"
          },
          {
            "role": "user",
            "type": "text",
            "content": que
          }
        ]

        r = chat_stream(messages,chat_url = model_url)
        print (r)
        if r.get("content"):
            code = r.get("content","")
            code_json = json.loads(code)
        if code_json.get("function") == "websearch":
            query = code_json.get("query")
            airsheet.write_xl(query, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        
        
    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4]
    ss = [sheetname]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=4)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
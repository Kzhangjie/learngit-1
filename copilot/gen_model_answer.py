from types import MethodType
from run_batch.run_ai import RunAi


file_id = "chmILwGYWvmo"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
必须有的列名 = ["prompts"] 
输出列名 = "模型返回"
输出列编号 = "AG"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api2 import Copilot
from code_session import chat_stream
model_url = "http://120.92.122.107:30818/kas/vbzjnuaoydcextkitrv9vj7yfrkv/api/chat/completions?model=latest"
def run_one(self,row):
    try:
        rs = []
        ds = {}
        prompts = json.loads(row["prompts"] +row.get("prompts1","")+row.get("prompts2","")+row.get("prompts3",""))
        for k,v in prompts.items():
            for i,messages in enumerate(v):
                r = chat_stream(messages,chat_url = model_url)
                rs.append(r)
                if k not in ds:
                    ds[k] = []
                if r.get("content"):
                    ds[k].append(r.get("content",""))
        result = json.dumps(rs,ensure_ascii=False,indent=4)
        dsr = json.dumps(ds,ensure_ascii=False,indent=4)
        airsheet.write_xl([result,dsr], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4]
    # ss = [sheetname1]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=4)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
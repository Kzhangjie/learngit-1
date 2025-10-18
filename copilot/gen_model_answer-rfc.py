from types import MethodType
from run_batch.run_ai import RunAi


file_id = "coqfCvWtT9n7"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
必须有的列名 = ["问题"] 
输出列名 = "session_id"
输出列编号 = "AG"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api2 import Copilot
from code_session import chat_stream
# model_url = "http://120.92.122.107:30818/kas/vbzjnuaoydcextkitrv9vj7yfrkv/api/chat/completions?model=latest"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api_rfc import Copilot
# cc = Copilot(is_test=True,model_url="http://10.8.254.24:30818/kas/vbzjnuaoydcextkitrv9vj7yfrkv/api/chat/completions?model=latest",custom_headers={})
cc = Copilot(is_test=True,model_url="http://kmd-api.kas.wps.cn/api/10783/BJfiZy/api/chat/completions")
cc.host = "127.0.0.1:5000"
def run_one(self,row):
    try:
        rs = []
        ds = {}
        prompts = json.loads(row["prompts"] +row.get("prompts1","")+row.get("prompts2","")+row.get("prompts3",""))
        num_prompts_keys = len(prompts.keys())
        
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        num_qs = len(qs)
        num_prompts_keys = len(prompts.keys())

        schedule_assertion_lines = row["调度断言"].split('\n')
        schedule_assertion_counts = [len(line.split()) for line in schedule_assertion_lines]
        all_conditions_met = True
        for i, (k, v) in enumerate(prompts.items()):
            if i < len(schedule_assertion_counts):
                if len(v) < schedule_assertion_counts[i]:
                    all_conditions_met = False
                    break
            else:
                all_conditions_met = False
                break
         
        if False:
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
        else:
            answer,logs,s_id = cc.questions(qs)
            result = json.dumps(answer,ensure_ascii=False,indent=4)
            r1 = result[:30000]
            r2 = result[30000:60000]
            r3 = result[60000:90000]
            r4 = result[90000:120000]
            log1 = logs[:30000]
            log2 = logs[30000:60000]
            log3 = logs[60000:90000]
            log4 = logs[90000:120000]
            # text = convert_messages_for_gpt(answer)
            text = ''
            # codes = extra_codes(answer)
            codes = ''
            airsheet.write_xl([f'\'{s_id}',r1,r2,r3,r4,log1,log2,log3,log4,text,codes], f'O{row["row_index"]}', sheet_name=self.sheetname)
        
    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4]
    # ss = [sheetname]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=5)
        ai.run_one = MethodType(run_one, ai)
        ai.run(10)
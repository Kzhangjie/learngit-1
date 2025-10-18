from types import MethodType
from run_batch.run_ai import RunAi


file_id = "cj0zKT3f7hYE"
sheetname = "websearch_验证集"
sheetname1 = "recommend_验证集"
# sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
sheetname5 = "help_验证集"
sheetname6 = "数理计算_验证集"
必须有的列名 = ["prompts"] 
输出列名 = "置信度最低分"
输出列编号 = "M"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api2 import Copilot
from code_session import chat_stream,chat_stream_logprob
model_url = "http://120.92.122.107:30818/kas/ybsjuqhgzi9-qkatvhtcdydnav5x/api/chat/completions?model=v2"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages
from api2 import Copilot

cc = Copilot(is_test=True,model_url="http://10.8.254.24:30818/kas/ybsjuqhgzi9-qkatvhtcdydnav5x/api/chat/completions?model=v2",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={})


def run_one(self,row):
    try:
        row_index = row["row_index"]
        prompts = json.loads(row["prompts"] +row.get("prompts1","")+row.get("prompts2","")+row.get("prompts3",""))
        # num_prompts_keys = len(prompts.keys())
        
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        # num_qs = len(qs)

        # schedule_assertion_lines = row["调度断言"].split('\n')
        # schedule_assertion_counts = [len(line.split()) for line in schedule_assertion_lines]
        # all_conditions_met = True
        # for i, (k, v) in enumerate(prompts.items()):
        #     if i < len(schedule_assertion_counts):
        #         if len(v) < schedule_assertion_counts[i]:
        #             all_conditions_met = False
        #             break
        #     else:
        #         all_conditions_met = False
        #         break

        model_answer_lops(self,prompts,row_index)
        # if num_qs == num_prompts_keys and all_conditions_met == True:
        #     model_answer_lops(self,prompts,row_index)
                      
        # else:
        #     history = row["WPS答案"] +row.get("WPS答案1","")+row.get("WPS答案2","")+row.get("WPS答案3","")
        #     history = json.loads(history)
        #     prompts = json.loads(history_to_prompt(self,history,qs,row_index))
        #     model_answer_lops(self,prompts,row_index)
            
    except Exception as e:
        print(traceback.format_exception(e))
        

def model_answer_lops(self,prompts,row_index):
    lps = {}
    low_lop = 1.00000
    for k,v in prompts.items():
        for i,messages in enumerate(v):
            max_retries = 3
            attempts = 0
            lp = chat_stream_logprob(messages,chat_url = model_url)
            while lp == {} and attempts < max_retries:
                attempts += 1
                print(f"第 {attempts} 次重试...")
                lp = chat_stream_logprob(messages, chat_url=model_url)
            if k not in lps:
                lps[k] = []
            if lp:
                lps[k].append(lp)
                if round(lp["func_prob"], 5) < low_lop:
                    low_lop = round(lp["func_prob"], 5)
    if all(len(v) == 0 for v in lps.values()):
        low_lop = ""
    lpsr = json.dumps(lps,ensure_ascii=False,indent=4)
    airsheet.write_xl([low_lop,lpsr], f'{self.clo_num_to_write}{row_index}', sheet_name=self.sheetname)
    return lpsr
    
def history_to_prompt(self,history,qs,row_index):
    messages = history_to_chat_messages(history,qs)
    prompt = json.dumps(messages,ensure_ascii=False,indent=2)
    prompt1 = prompt[:30000]
    prompt2 = prompt[30000:60000]
    prompt3 = prompt[60000:90000]
    prompt4 = prompt[90000:120000]
    airsheet.write_xl([prompt1,prompt2,prompt3,prompt4], f'AC{row_index}', sheet_name=self.sheetname)
    return prompt


if __name__ == '__main__':
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname6]
    ss = [sheetname3]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=4)
        ai.run_one = MethodType(run_one, ai)
        ai.run(1)
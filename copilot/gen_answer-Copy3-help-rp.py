from types import MethodType
from run_batch.run_ai import RunAi
from itertools import islice
import requests


file_id = "cgwX07LRHg4j"
sheetname6 = "【20250310】全部_zrp_短文"
# 闲聊 创作 反馈群
# sheetname = "豆包"
# sheetname6 = "tencent,doubao"


必须有的列名 = ["问题"] 
输出列名 = "code1"
输出列编号 = "L"
# 新版本回答C 旧版本回答E MM版本回答G MM6.5版本回答I

# 输出列名 = "新版本-message1"
# 输出列编号 = "M"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages,history_to_model_messages
from api2 import Copilot
from retry import retry
cc = Copilot(is_test=True,model_url="",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={},search_engines="")
import logging
logging.basicConfig()
@retry(tries=10, delay=1, backoff=1.5, jitter=(0, 3))
def send_request(id,data):
    rpurl = "http://10.13.147.249:8000/help"
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(rpurl, headers=headers, data=json.dumps(data))
    if response.status_code!=200:
        print(id)
        print(response.text)
        response.raise_for_status() 
    return response.json()
def run_one(self,row):
    headers = {
            "Content-Type": "application/json"
        }
        
    

    reall = []
    
    try:
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        try: 
            prompts = json.loads(row["prompts"] +row.get("prompts1","")+row.get("prompts2","")+row.get("prompts3",""))
            for k,v in prompts.items():
                data = {
                    "messages": v[0]
                }
                # print ("======================")
                # print (data)
                # print ("======================")
                # response = requests.post(rpurl, headers=headers, data=json.dumps(data))
                # print (respons)
                try:
                    res = send_request(row['用例编号'],data)
                except Execption as e:
                    print(f"用例编号{row['用例编号']}错误：{e}")
                content = res.get("response","")
                code = json.dumps(res.get("code",{}),ensure_ascii=False,indent=4)
                messages = json.dumps(res.get("messages",{}),ensure_ascii=False,indent=4)
                reall.append(code)
                reall.append(content)
                reall.append(messages)
            airsheet.write_xl(reall, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)      
        except json.JSONDecodeError:
            print ("prompt解析失败，直接跑工程接口")
                
                # for i,messages in enumerate(v):
        # print (qs)
        # answer,logs,s_id = cc.questions(qs)
        # data = {
        #     "messages": [
        #         {
        #             "role": "system",
        #             "type": "text",
        #             "content": "今天是:2025-03-03。"
        #         },
        #         {
        #             "role": "user",
        #             "type": "text",
        #             "content": qs[0]
        #         }
        #     ],
        #     "stream": False
        # }
        # headers = {
        #     "Content-Type": "application/json"
        # }
        
        # rpurl = "http://10.13.147.249:8000/help"
        # try:
        #     response = requests.post(rpurl, headers=headers, data=json.dumps(data))
        #     # response.raise_for_status()
        #     # response.encoding = 'utf-8'
        #     print (response)
        #     res = response.json()
        #     content = res.get("response","")
        #     code = json.dumps(res.get("code",{}),ensure_ascii=False,indent=4)
        #     messages = json.dumps(res.get("messages",{}),ensure_ascii=False,indent=4)
        #     airsheet.write_xl([code,content,messages], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)

        
        # except requests.exceptions.RequestException as e:
        #     print(f"Request failed: {e}")

        
        
        # content = next(
        #     msg["content"]
        #     for msg in islice(reversed(answer.get("data", {}).get("list", [])), 1, None)  # 跳过第一个，返回第二个
        #     if msg.get("role") == "assistant"
        # )
        # code = next(
        #     (msg["content"] for msg in answer.get("data", {}).get("list", []) if msg.get("type") == "code"),
        #     None  # 如果没有找到符合条件的消息，返回 None
        # )
        # reason = next(
        #     (msg["content"] for msg in answer.get("data", {}).get("list", []) if msg.get("type") == "reasoning"),
        #     None  # 如果没有找到符合条件的消息，返回 None
        # )
        # if reason:
        #      reason = json.loads(reason).get("text","")
        # airsheet.write_xl([code,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl(content, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([r1,r2,r3,r4,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([m1,m2,m3,m4,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)

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
from types import MethodType
from run_batch.run_ai import RunAi
from itertools import islice


file_id = "cdSMmmrq9RMB"
sheetname = "pdf"
sheetname1 = "ppt"
sheetname2 = "wps"
sheetname3 = "wps-online"
# sheetname4 = "chat_验证集"
# sheetname5 = "人设_验证集"
# sheetname6 = "反馈群"
# 闲聊 创作 反馈群
# sheetname = "豆包"
# sheetname6 = "tencent,doubao"


必须有的列名 = ["filename"] 
输出列名 = "推荐问题"
输出列编号 = "E"
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
cc = Copilot(is_test=True,model_url="",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={},search_engines="")
def run_one(self,row):
    
    try:
        # qs = row["问题"].split("ask:")
        # qs = [q.strip() for q in qs if q]
        # print (qs)
        # answer,logs,s_id = cc.questions(qs)
        filetype = row.get("type","")
        filename = row.get("filename","")
        fileid = ""
        recommend_str = cc.canvas_recommend(filename,fileid,filetype)
        airsheet.write_xl(recommend_str, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        
        
        
        # content = next(
        #     msg["content"]
        #     for msg in islice(reversed(answer.get("data", {}).get("list", [])), 1, None)  # 跳过第一个，返回第二个
        #     if msg.get("role") == "assistant"
        # )
        # reason = next(
        #     (msg["content"] for msg in answer.get("data", {}).get("list", []) if msg.get("type") == "reasoning"),
        #     None  # 如果没有找到符合条件的消息，返回 None
        # )
        # if reason:
        #      reason = json.loads(reason).get("text","")
        # airsheet.write_xl([reason,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl(content, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([r1,r2,r3,r4,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
        # airsheet.write_xl([m1,m2,m3,m4,content], f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)

    except Exception as e:
        print(traceback.format_exception(e))

if __name__ == '__main__':
    # ss = [sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname]
    ss = [sheetname,sheetname1,sheetname2,sheetname3]
    # ss = [sheetname5]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=5)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
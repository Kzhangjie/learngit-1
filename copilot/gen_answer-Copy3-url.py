from types import MethodType
from run_batch.run_ai import RunAi
from itertools import islice


file_id = "cemYV0SchN90"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
sheetname5 = "人设_验证集"
sheetname6 = "用例"
# sheetname = "豆包"
# sheetname6 = "tencent,doubao"


必须有的列名 = ["问题"] 
输出列名 = "豆包新版本回答"
输出列编号 = "K"
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
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        # print (qs)
        answer,logs,s_id = cc.questions(qs)
        # fileinfo = row["文件url内容"]
        result = json.dumps(answer,ensure_ascii=False,indent=4)
        r1 = result[:30000]
        r2 = result[30000:60000]
        r3 = result[60000:90000]
        r4 = result[90000:120000]

        # message = history_to_model_messages(answer,fileinfo)
        # model_message = json.dumps(message,ensure_ascii=False,indent=4)     
        # m1 = model_message[:30000]
        # m2 = model_message[30000:60000]
        # m3 = model_message[60000:90000]
        # m4 = model_message[90000:120000]
        # content = next(msg["content"] for msg in reversed(json.loads(answer)) if msg["role"] == "assistant" and msg["type"] == "text")
        content = next(
            msg["content"]
            for msg in islice(reversed(answer.get("data", {}).get("list", [])), 1, None)  # 跳过第一个，返回第二个
            if msg.get("role") == "assistant"
        )
        airsheet.write_xl(content, f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)
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
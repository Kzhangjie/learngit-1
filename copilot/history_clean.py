from types import MethodType
from run_batch.run_ai import RunAi
import re
import traceback
from run_batch.code_utils.validate_json_in_text import extract_json_from_text
from run_batch.run_code import RunCode


file_id = "cswUi1Y4l6Zq"
sheetname = "websearch_验证集"
sheetname1 = "recommend_验证集"
# sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
sheetname5 = "help_验证集"
sheetname6 = "数理计算_验证集"
sheetname7 = "mindmap_验证集"
sheetname8 = "image_验证集"
sheetname9 = "chat_验证集 (2)"
必须有的列名 = ["prompts"] 
输出列名 = ""
输出列编号 = "AC"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api2 import Copilot
from code_session import chat_stream,chat_stream_logprob
#公网url
model_url = "http://120.92.122.107:30818/kas/wherg1vn9kgl1eghn5ws6f2rbezl/api/chat/completions?model=lingxi_g7_e10"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages
from api2 import Copilot
#内网url
cc = Copilot(is_test=True,model_url="http://10.8.254.24:30818/kas/wherg1vn9kgl1eghn5ws6f2rbezl/api/chat/completions?model=lingxi_g7_e10",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={})

def run_one(self,row):
    try: 
        prompts = json.loads(row["prompts"] +row.get("prompts1","")+row.get("prompts2","")+row.get("prompts3",""))
        for i, (k, v) in enumerate(prompts.items()):
            for sub_list in v:
                for item in sub_list:
                    if item.get("type") == "code":
                        # 解析content为JSON
                        code_content = json.loads(item["content"])
                        if code_content.get("function") == "websearch":
                            # 删除 query_tag 和 recency_days
                            code_content.pop("query_tag", None)
                            code_content.pop("recency_days", None)
                            # 更新回去
                            item["content"] = json.dumps(code_content, ensure_ascii=False)
                            
        new_prompts = json.dumps(prompts,indent=2, ensure_ascii=False)
        prompt1 = new_prompts[:30000]
        prompt2 = new_prompts[30000:60000]
        prompt3 = new_prompts[60000:90000]
        prompt4 = new_prompts[90000:120000]
        airsheet.write_xl([prompt1,prompt2,prompt3,prompt4],f'{self.clo_num_to_write}{row["row_index"]}', sheet_name=self.sheetname)

    except json.JSONDecodeError:
        print ("prompt解析失败，直接跑工程接口")

if __name__ == '__main__':
    ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname6,sheetname7,sheetname8]
    # ss = [sheetname2,sheetname3,sheetname4,sheetname5]
    # ss = [sheetname]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=6)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
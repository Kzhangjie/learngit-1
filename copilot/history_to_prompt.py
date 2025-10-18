
import re
import traceback
from run_batch.code_utils.validate_json_in_text import extract_json_from_text
from run_batch.run_code import RunCode

file_id = "crI9GjxjuQ5V"
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
必须有的列名 = ["WPS答案"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "prompts" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "AC" # 表示从把答案写到C列
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
import json
from copilot.code_session import history_to_chat_messages, history_to_canvas_messages
import re    
def run_one(row:dict):
    history = row["WPS答案"] +row.get("WPS答案1","")+row.get("WPS答案2","")+row.get("WPS答案3","")
    history = json.loads(history)
    qs = row["问题"].split("ask:")
    qs = [q.strip() for q in qs if q]
    messages = history_to_chat_messages(history,qs)
    prompt = json.dumps(messages,ensure_ascii=False,indent=2)
    prompt1 = prompt[:30000]
    prompt2 = prompt[30000:60000]
    prompt3 = prompt[60000:90000]
    prompt4 = prompt[90000:120000]
    
    return [prompt1,prompt2,prompt3,prompt4]

if __name__ == "__main__":
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4]
    ss = [sheetname4]
    for s in ss:
        code = RunCode(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
        code.run_one = run_one
        code.run()
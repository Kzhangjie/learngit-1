import re
import traceback
from run_batch.code_utils.validate_json_in_text import extract_json_from_text
from run_batch.run_code import RunCode

file_id = "chMCLGCfF4Ih"
sheetname = "保存PPT_验证集"  
必须有的列名 = ["WPS答案"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "U" # 表示从把答案写到C列
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
import json

def parse_keywrod(text):
    text = text.strip()
    ts = text.split("\n")
    ts = [t.strip() for t in ts]
    ts = [t for t in ts if t]
    return ts
from gen_prompt import gen_question_answer_pairs
def dispatch_ok(qaps:list,ks:str,keyword:str):
    kws = parse_keywrod(ks)
    ok = True
    for index,qap in enumerate(qaps):
        asfs = qap.get("a",[])
        codes = [a["content"] for a in asfs if a["type"] == "code"]
        contain_keyword = any([d.startswith('{\"function\": \"'+keyword+'\"')  for d in codes])
        search = kws[index] if index < len(kws) else ""
        if search == "是":
            ok = contain_keyword
        elif search == "否":
            ok = not contain_keyword
        else:
            continue
        if not ok:
            break
    return "是" if ok else "否"
    
def run_one(row:dict):
    qaps = gen_question_answer_pairs(json.loads(row["WPS答案"]))
    try:
        search_ok = dispatch_ok(qaps,row.get("是否需要websearch",""),keyword="websearch")
    except Exception as e:
        print("解析匹配是否需要websearch出错",traceback.format_exception(e))
        search_ok = "error"
    try:
        save_ok = dispatch_ok(qaps,row.get("是否需要创建文件",""),keyword="create_file")
    except Exception as e:
        print("解析匹配是否需要创建文件出错",traceback.format_exception(e))
        save_ok = "error"
    try:
        fetch_ok = dispatch_ok(qaps,row.get("是否需要url_fetch",""),keyword="url_fetch")
    except Exception as e:
        print("解析匹配是否需要url_fetch",traceback.format_exception(e))
        fetch_ok = "error"
    return [search_ok,save_ok,fetch_ok]

if __name__ == "__main__":
    code = RunCode(file_id=file_id,sheetname=sheetname,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
    code.run_one = run_one
    code.run()
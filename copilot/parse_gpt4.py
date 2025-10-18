import re
from run_batch.code_utils.validate_json_in_text import extract_json_from_text
from run_batch.run_code import RunCode

file_id = "ckIo5P74CaXT"
sheetname = "websearch_rfc"  
必须有的列名 = ["GPT测试详情"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "Y" # 表示从把答案写到C列
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
import json

def all_pass(datas):
    for data in datas:
        if data["是否通过"] != "是":
            return False
    return True

def extract_answer(text):
    json_str = extract_json_from_text(text)
    result = json.loads(json_str)
    总体是否通过 = result["总体是否通过"]
    其他明显缺陷 = result["其他明显缺陷"]
    checklist结果 = result["checklist结果"]
    humans = checklist结果[:-4]
    commons = checklist结果[-4:]
    # print(111,commons)
    
    commons_pass = ['是' if c['是否通过'] == '是' else c['理由'] for c in commons]
    search = [s for s in humans if "websearch" in s["要求描述"]]
    search_pass = all_pass(search)
    saves = [s for s in humans if "create_file" in s["要求描述"]]
    saves_pass = all_pass(saves)
    fetchs = [s for s in humans if "url_fetch" in s["要求描述"]]
    fetchs_pass = all_pass(fetchs)
    ans = [s for s in humans if ("websearch" not in s["要求描述"] and "create_file" not in s["要求描述"] and "url_fetch" not in s["要求描述"])]
    ans_pass = all_pass(ans)
    return [总体是否通过,search_pass,saves_pass,fetchs_pass,ans_pass,commons_pass[0],commons_pass[1],commons_pass[2],commons_pass[3],其他明显缺陷]

def run_one(row):
    a =  extract_answer(row["GPT测试详情"])
    return a

if __name__ == "__main__":
    code = RunCode(file_id=file_id,sheetname=sheetname,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
    code.run_one = run_one
    code.run()
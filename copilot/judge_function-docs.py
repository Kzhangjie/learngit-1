import re
import traceback
from run_batch.code_utils.validate_json_in_text import extract_json_from_text
from run_batch.run_code import RunCode

file_id = "cu4n6bXGLFKp"
sheetname = "websearch_验证集"
sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
必须有的列名 = ["LOGS调度结果"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "模型调度断言总体" # 表示会跳过"答案"列已经有内容的行。
输出列编号 = "AI" # 表示从把答案写到C列
WPS_SID = None
# WPS_SID = "你的WPS_SID" # 如果不想给任方超文档编辑权限，求去掉这行注释，传入自己WPS_SID
import json

import re    
def run_one(row:dict):
    ans_len = len(row["问题"].split("ask:")) -1 
    checks = row["调度断言"].strip().split("\n")
    checks = checks + [""] * (ans_len - len(checks))
    checks = [re.split(r'\s+', c.strip()) for c in checks]
    codes = json.loads(row["LOGS调度结果"])
    for k,v in codes.items():
        functions = []
        for code in v:
            functions.append(json.loads(code)["function"])
        codes[k] = functions
        
    ok = "是"
    details = []
    for index,check in enumerate(checks):
        print(index,111,check,codes)
        if check == ["空"]:
            continue
        code = codes.get(str(index+1),[])
        for c in check:
            if c.startswith("-"):
                c = c[1:]
                if c in code:
                    ok = "否"
                    details.append(f"第{index + 1}个回答不应该包含{c}")
            elif c and c not in code:
                # print(333,c ,code)
                ok = "否"
                details.append(f"第{index+1}个回答没有{c}")
    return [ok,"\n".join(details)]

if __name__ == "__main__":
    ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4]
    # ss = [sheetname2]
    for s in ss:
        code = RunCode(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
        code.run_one = run_one
        code.run()
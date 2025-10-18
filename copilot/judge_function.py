import re
import traceback
from run_batch.code_utils.validate_json_in_text import extract_json_from_text
from run_batch.run_code import RunCode

file_id = "ciHNh8ezZ27T"
sheetname = "websearch_验证集"
sheetname1 = "recommend_验证集"
# sheetname1 = "创建文件_验证集"
sheetname2 = "保存PPT_验证集"
sheetname3 = "URL_fetch_验证集"
sheetname4 = "chat_验证集"
sheetname5 = "help_验证集"
sheetname6 = "数理计算_验证集"
sheetname7 = "mindmap_验证集"
必须有的列名 = ["模型调度结果"] # 表示会跳过用例编号为空的行，可以多个，可根据需求修改
输出列名 = "" # 表示会跳过"答案"列已经有内容的行。
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
    print (checks)
    codes = json.loads(row["模型调度结果"])
    # row_index = row["row_index"]

    
    # judge_function(self,codes,checks,row_index,answer_type):
    
    
    functions = {}
    deepsearchs = {}
    longwrites = {}
    for k,v in codes.items():
        # print("提取function打印v的内容",v)
        function = []
        for code in v:
            function.append(json.loads(code)["function"])
        functions[k] = function
        
    for k, v in codes.items():
        print("打印v的内容",v)
        function_web = []
        function_chat = []
        for c in v:
            # print ("打印此时的code内容",c)
            parsed_code = json.loads(c)
            if parsed_code["function"] == "websearch":
                function_web.append(str(parsed_code.get("deep_search", "无")))  
            elif parsed_code["function"] == "chat":
                function_chat.append(str(parsed_code.get("longwrite", "无")))  
            else:
                function_web.append("无")  # 在else的情况下追加None
                function_chat.append("无")  # 在else的情况下追加None
        deepsearchs[k] = function_web
        longwrites[k] = function_chat
        
    ok = "是"
    details = []
    
    for index, check in enumerate(checks):
        code = functions.get(str(index + 1), [])
        deepsearch = deepsearchs.get(str(index + 1), [])
        longwrite = longwrites.get(str(index + 1), [])
        # 跟踪检查过的 code 项
        checked_codes = []
    
        for c in check:
            if "/" in c:  # 新增规则 1，拆分中间带有/的情况
                parts = c.split("/")
                if not any(part in code for part in parts):
                    ok = "否"
                    details.append(f"第{index + 1}个回答没有满足{c}中的任意一项")
                else:
                    matched_parts = [part for part in parts if part in code]
                    checked_codes.extend(matched_parts)
                #     checked_codes.extend(parts)
                # checked_codes.append(c)
                continue  # 一旦处理了 / 的情况，跳过本次循环
    
            if c.startswith("websearch"):
                if c.endswith("-deepsearch"):
                    if "True" not in deepsearch:
                        ok = "否"
                        details.append(f"第{index + 1}个回答没有deepsearch")
                elif c == "websearch":
                    if "True" in deepsearch:
                        ok = "否"
                        details.append(f"第{index + 1}个回答不应该有deepsearch")
                    elif c not in code:
                        ok = "否"
                        details.append(f"第{index + 1}个回答没有{c}")
                checked_codes.append("websearch")
            elif c.startswith("chat"):
                if c.endswith("-longwrite"):
                    if "True" not in longwrite:
                        ok = "否"
                        details.append(f"第{index + 1}个回答没有longwrite")
                elif c == "chat":
                    if "True" in longwrite:
                        ok = "否"
                        details.append(f"第{index + 1}个回答不应该有longwrite")
                    elif c not in code:
                        ok = "否"
                        details.append(f"第{index + 1}个回答没有{c}")
                checked_codes.append("chat")
            else:
                if c and c not in code:  # 保留原始规则，检查是否在code里
                    ok = "否"
                    details.append(f"第{index + 1}个回答没有{c}")
                else:
                    checked_codes.append(c)
    
    # if ok == "是":
        extra_codes = []
        for c in code:
            # if "-" in c:
            #     c = c.split("-")[0]  # 取 - 前面的部分
            if c not in checked_codes:
                extra_codes.append(c)
        if extra_codes:
            ok = "否"
            details.append(f"第{index + 1}个回答多了{', '.join(extra_codes)}")

    # if answer_type == True:
    #     airsheet.write_xl([ok,"\n".join(details)], f'AA{row_index}', sheet_name=self.sheetname)
    # else:
    # airsheet.write_xl([ok,"\n".join(details)], f'AI{row["row_index"]}', sheet_name=self.sheetname)
    return [ok,"\n".join(details)]

if __name__ == "__main__":
    ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname6,sheetname7]
    # ss = [sheetname1]
    for s in ss:
        code = RunCode(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,wps_sid=WPS_SID)
        code.run_one = run_one
        code.run()
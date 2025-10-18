from types import MethodType
from run_batch.run_ai import RunAi
import re
import traceback
from run_batch.code_utils.validate_json_in_text import extract_json_from_text
from run_batch.run_code import RunCode


file_id = "cs8MMQEOnmpy"
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
sheetname9 = "搜图_验证集"
必须有的列名 = ["prompts"] 
输出列名 = "模型返回"
输出列编号 = "AG"

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes
from api2 import Copilot
from copilot.code_session import chat_stream,chat_stream_logprob
#公网url
model_url = ""


# http://120.92.122.107:30818/kas/bmfcacd11vhnv7crjzzq1y4mnena/api/chat/completions?model=canvas
# http://10.8.254.24:30818/kas/bmfcacd11vhnv7crjzzq1y4mnena/api/chat/completions?model=canvas

# http://120.92.122.107:30818/kas/bmfcacd11vhnv7crjzzq1y4mnena/api/chat/completions?model=canvas_remove
#公网 http://120.92.122.107:30818/kas/ybsjuqhgzi9-qkatvhtcdydnav5x/api/chat/completions?model=canvas
#内网 http://10.8.254.24:30818/kas/ybsjuqhgzi9-qkatvhtcdydnav5x/api/chat/completions?model=canvas

from api import questions
import airsheet
import traceback
import json
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages,history_to_canvas_messages
from api2 import Copilot
#内网url
cc = Copilot(is_test=True,model_url="",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={})


def run_one(self,row):
    try:
        file_urls = row["预设文件"]
        print (file_urls)
        file_data={}
        if file_urls:
            file_data = fileids(file_urls)
            print (file_data)
        
        answer_type = False
        ans_len = len(row["问题"].split("ask:")) -1 
        row_index = row["row_index"]
        checks = row["调度断言"].strip().split("\n")
        checks = checks + [""] * (ans_len - len(checks))
        checks = [re.split(r'\s+', c.strip()) for c in checks]
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]
        if file_data:
            qs = process_questions(qs, file_data)
        print (qs)
        num_qs = len(qs)
        print (checks)
        try: 
            prompts = json.loads(row["prompts"] +row.get("prompts1","")+row.get("prompts2","")+row.get("prompts3",""))
            num_prompts_keys = len(prompts.keys())
            
            schedule_assertion_lines = row["调度断言"].split('\n')
            schedule_assertion_counts = [len(line.split()) for line in schedule_assertion_lines]
            all_conditions_met = True
            for i, (k, v) in enumerate(prompts.items()):
                if i < len(schedule_assertion_counts):
                    if len(v) < schedule_assertion_counts[i]:
                        all_conditions_met = False
                        break
                else:
                    all_conditions_met = False
                    break
             
            # if num_qs == num_prompts_keys and all_conditions_met == True:
            if num_prompts_keys != 0 and all_conditions_met == True:
                codes = json.loads(model_answer(self,prompts,row_index))
                function_ans = judge_function(self,codes,checks,row_index,answer_type)
                
                if function_ans[0] == "否" and self.sheetname not in { "chat_验证集","help_验证集","数理计算_验证集", "image_验证集"} :
                    if num_qs != len(codes.keys()):
                        answer_type = False
                    else:
                        answer_type = True
                    codes = json.loads(answer(self,qs,row_index,answer_type))
                    function_ans = judge_function(self,codes,checks,row_index,answer_type)
                          
            else:
                codes = json.loads(answer(self,qs,row_index,answer_type))
                function_ans = judge_function(self,codes,checks,row_index,answer_type)
        
        except json.JSONDecodeError:
            print ("prompt解析失败，直接跑工程接口")
            codes = json.loads(answer(self,qs,row_index,answer_type))
            function_ans = judge_function(self,codes,checks,row_index,answer_type)
            
    except Exception as e:
        print(traceback.format_exception(e))

def fileids(text):
    valid_canvas = {"PDFcanvas", "WPPcanvas", "ETcanvas", "WPScanvas"}
    data = {}
    current_index = None  # 记录当前处理的序号
    text = text.replace("：", ":").replace("\r\n", "\n").strip()
    for line in text.split("\n"):
        line = line.strip()  # 清除前后空格，避免匹配问题
        print ("行内容",line)

        # 匹配 "序号：名称 链接" 形式
        match = re.search(r"^(\d+):(\S*)\s*(https://kdocs\.cn/l/[\w]+)", line)
        
        if match:
            index, canvas, link = match.groups()
            fid = link.split("/")[-1]
            current_index = index  # 更新当前处理的序号
            
            # 初始化该序号的数据
            if index not in data:
                data[index] = {"canvas": "", "fids": []}

            # 仅当 canvas 合法时赋值
            if canvas in valid_canvas:
                data[index]["canvas"] = canvas

            # 添加链接 ID
            data[index]["fids"].append(fid)
            continue  # 进入下一个循环

        # 匹配单独的链接（无序号）
        match_link = re.search(r"https://www\.kdocs\.cn/l/([\w]+)", line)
        if match_link and current_index:
            fid = match_link.group(1)
            data[current_index]["fids"].append(fid)

    return data

def process_questions(qs, data):
    result_qs = []
    print ("问题列表",qs)
    print ("文件链接列表",data)

    for i, q in enumerate(qs, start=1):  # 从 1 开始匹配序号
        index = str(i)
        q = q.strip()  # 去除问题前后空格

        if index in data:  # 只有 data 里存在该序号时才处理
            canvas = data[index]["canvas"]
            fids = data[index]["fids"]

            # 处理 fids 追加部分
            file_links = []
            for fid in fids:
                if canvas:  # canvas 不为空
                    file_links.append(f"[文件名]({canvas})(wps365://files/{fid})")
                else:  # canvas 为空
                    file_links.append(f"[文件名](wps365://files/{fid})")

            # 拼接 fids 信息到当前问题前面
            print("file_links:", file_links)
            fids_str = " ".join(file_links)  # 多个 fids 之间用空格连接
            print("file_links_str:", fids_str)  
            q = f"{fids_str} {q}" if fids_str else q  # 如果 fids_str 为空，就不拼接

        result_qs.append(q)

    return result_qs
    
    

def answer(self,qs,row_index,answer_type):
    
    answer,logs,s_id = cc.questions(qs)
    result = json.dumps(answer,ensure_ascii=False,indent=4)
    r1 = result[:30000]
    r2 = result[30000:60000]
    r3 = result[60000:90000]
    r4 = result[90000:120000]
    # log1 = logs[:30000]
    # log2 = logs[30000:60000]
    # log3 = logs[60000:90000]
    # log4 = logs[90000:120000]
    log1 = ""
    log2 = ""
    log3 = ""
    log4 = ""
    # text = convert_messages_for_gpt(answer)
    text = {
        "data": {
            "list": trans_chat_messages_2_messages(answer.get("data", {}).get("list", []), qs)
        },
        "result": answer.get("result")
    }
    
    new_text = json.dumps(text, ensure_ascii=False, indent=2)
    codes = extra_codes(answer)
    # codes = ''
    codes_in_logs = extra_codes_from_logs(json.loads(logs))
    prompt = history_to_prompt(self,answer,qs,row_index)
    airsheet.write_xl([f'\'{s_id}',r1,r2,r3,r4,log1,log2,log3,log4,new_text,codes,codes_in_logs], f'O{row_index}', sheet_name=self.sheetname)
    if answer_type == False:
        airsheet.write_xl(["",codes_in_logs], f'AG{row_index}', sheet_name=self.sheetname)
    # airsheet.write_xl([codes], f'AH{row_index}', sheet_name=self.sheetname)
    # return  codes
    return  codes_in_logs

def model_answer(self,prompts,row_index):
    rs = []
    ds = {}
    for k,v in prompts.items():
        for i,messages in enumerate(v):
            # 
            r = chat_stream(messages,chat_url = model_url)
            print (r)
            rs.append(r)
            if k not in ds:
                ds[k] = []
            if r.get("content"):
                ds[k].append(r.get("content",""))
    result = json.dumps(rs,ensure_ascii=False,indent=4)
    dsr = json.dumps(ds,ensure_ascii=False,indent=4)
    airsheet.write_xl([result,dsr], f'{self.clo_num_to_write}{row_index}', sheet_name=self.sheetname)
    return dsr
    
def judge_function(self,codes,checks,row_index,answer_type):
    functions = {}
    deepsearchs = {}
    longwrites = {}
    help_querys = {}
    for k,v in codes.items():
        # print("提取function打印v的内容",v)
        function = []
        for code in v:
            function.append(json.loads(code)["function"])
        functions[k] = function
        
    for k, v in codes.items():
        function_web = []
        function_chat = [] 
        function_help = []
        print("打印v的内容",v)
        for c in v:
            # print ("打印此时的code内容",c)
            parsed_code = json.loads(c)
            if parsed_code["function"] == "websearch":
                function_web.append(str(parsed_code.get("deep_search", "无")))  
                tag = parsed_code.get("query_tags", "[f'无']")
                function_help.append(str(tag[0]))
                function_chat.append("无") 
                # function_help.append("无")
            elif parsed_code["function"] == "chat":
                function_chat.append(str(parsed_code.get("longwrite", "无")))  
                function_web.append("无")  
                function_help.append("无")
            elif parsed_code["function"] == "help":
                tag = parsed_code.get("query_tags", "[f'无']")
                function_help.append(str(tag[0]))
                function_chat.append("无") 
                function_web.append("无") 
            else:
                function_web.append("无")  
                function_chat.append("无")  
                function_help.append("无")
        deepsearchs[k] = function_web
        longwrites[k] = function_chat
        help_querys[k] = function_help
        

    # print ("==========深度搜索、长文写作的code==================================================")
    # print (deepsearchs)
    # print (longwrites)
    # print ("==========深度搜索、长文写作的code==================================================")
        
    ok = "是"
    details = []
    
    for index, check in enumerate(checks):
        code = functions.get(str(index + 1), [])
        deepsearch = deepsearchs.get(str(index + 1), [])
        longwrite = longwrites.get(str(index + 1), [])
        help_query = help_querys.get(str(index + 1), [])
        
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
                elif c.endswith("-人设"):
                    if "人设" not in help_query:
                        ok = "否"
                        details.append(f"第{index + 1}个回答help没有人设")
                elif c.endswith("-wps"):
                    if "wps" not in help_query:
                        ok = "否"
                        details.append(f"第{index + 1}个回答help没有WPS")
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
                
            elif c.startswith("help"):
                if c.endswith("-人设"):
                    if "人设" not in help_query:
                        ok = "否"
                        details.append(f"第{index + 1}个回答help没有人设")
                elif c.endswith("-wps"):
                    if "wps" not in help_query:
                        ok = "否"
                        details.append(f"第{index + 1}个回答help没有WPS")
                elif c == "help":
                    if c not in code:   
                            ok = "否"
                            details.append(f"第{index + 1}个回答没有{c}")
                checked_codes.append("help")
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

    if answer_type == True:
        airsheet.write_xl([ok,"\n".join(details)], f'AA{row_index}', sheet_name=self.sheetname)
    else:
        airsheet.write_xl([ok,"\n".join(details)], f'AI{row_index}', sheet_name=self.sheetname)
    return [ok,"\n".join(details)]
    
def history_to_prompt(self,history: dict,qs,row_index):
    messages = history_to_canvas_messages(history,qs)
    prompt = json.dumps(messages,ensure_ascii=False,indent=2)
    prompt1 = prompt[:30000]
    prompt2 = prompt[30000:60000]
    prompt3 = prompt[60000:90000]
    prompt4 = prompt[90000:120000]
    airsheet.write_xl([prompt1,prompt2,prompt3,prompt4], f'AC{row_index}', sheet_name=self.sheetname)
    return prompt

if __name__ == '__main__':
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname6,sheetname7,sheetname8]
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname5,sheetname4,sheetname7,sheetname8] 
    # ss = [sheetname,sheetname2,sheetname3,sheetname4,sheetname5,sheetname7,sheetname8]
    # ss = [sheetname9,sheetname4,sheetname3,sheetname8,sheetname,sheetname2,sheetname7] #canvas用例评测
    ss = [sheetname7]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=6)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
import json
import logging
import time
from datetime import date
from datetime import datetime
from typing import Generator, List, Dict
import math
import xml.etree.ElementTree as ET
import requests
import sseclient
import typing
from dataclasses import dataclass, field
from typing import List, Literal, Optional
from copilot.cutting import Cutter
from copilot.crawl import url_fetch
import re
import copy
import xml.etree.ElementTree as ET
filelink_pattern = re.compile(r"\[([^\]]+)\]\(wps365://files/([^\)]+)\)")

today = date.today()
weekday = today.weekday()
weekdays_cn = "一二三四五六日"
systemtoday = today.strftime(f'%Y-%m-%d')
# modeltoday = datetime.now().strftime("%Y 年 %m 月 %d 日 %A")
def _get_current_date_desc() -> str:
    # 获取当前时间
    now = datetime.now()
    # 英文星期转中文星期的映射
    day_map = {
        "Monday": "星期一",
        "Tuesday": "星期二",
        "Wednesday": "星期三",
        "Thursday": "星期四",
        "Friday": "星期五",
        "Saturday": "星期六",
        "Sunday": "星期日",
    }
    # 获取英文星期名称
    english_day = now.strftime("%A")
    # 映射为中文
    chinese_day = day_map[english_day]
    # 格式化日期并附加中文星期
    current_date_desc = now.strftime(f"%Y 年 %m 月 %d 日 {chinese_day}")
    return current_date_desc
modeltoday = _get_current_date_desc()

def findall_filelinks(prompt:str) -> dict:
    links = {}
    for m in filelink_pattern.findall(prompt):
        print(333,m)
        links[m[1]] = m[0]
    return links
def trans_chat_messages_2_messages(messages: List[dict],qs: List[str]):
    打开搜索 = '''# 工具信息\n你可以调用一个或多个工具来处理用户的请求，支持的工具签名如下:\n<tools>\n{\"name\": \"chat\", \"description\": \"用于普通问答。当用户请求不符合其他工具的要求时，应调用此工具。\"}\n{\"name\": \"websearch\", \"description\": \"用于信息检索。若用户请求需要获取实时、最新信息、人设信息时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"搜索关键字。可包含多组关键词，关键词之间用空格区分；如需获取特定时效性信息，需在关键词中加上相应时间范围；如请求涉及人设信息提问时，使用“WPS灵犀”指代你。\"}, \"prompt\": {\"type\": \"string\", \"description\": \"该参数用于在多工具调用场景下，对用户请求中的搜索意图进行识别提取，确保能准确处理相关操作。\"}, \"extra_querys\": {\"type\": \"array\", \"description\": \"若用户请求过于复杂，需要多次搜索保证回答效果时，使用该参数进行描述。\", \"items\": {\"type\": \"string\", \"description\": \"多次搜索关键字。\"}}, \"query_tags\": {\"type\": \"array\", \"description\": \"搜索标签，用户请求与WPS组件能力或人设信息相关时，应使用此参数标识。\", \"items\": {\"type\": \"string\", \"description\": \"询问与wps组件能力相关信息时，使用“wps”标签，与人设信息相关时，使用“人设”标签。\", \"enum\": [\"wps\", \"人设\"]}}, \"deep_search\": {\"type\": \"bool\", \"description\": \"若用户请求希望对问题进行深度剖析时，该参数为true。\"}}, \"required\": [\"query\"]}}\n{\"name\": \"url_fetch\", \"description\": \"用于提取超链接对应的网站信息。当用户请求包含超链接并希望对其提供的合法超链接进行信息提取时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"prompt\": {\"type\": \"string\", \"description\": \"该参数用于在多工具调用场景下，对用户请求中的超链接信息提取意图进行识别提取，确保能准确处理相关操作。\"}}}}\n{\"name\": \"generate_image\", \"description\": \"用于生成有明确主题的艺术类图片。若用户请求需要生成或润色艺术类，且有明确的主题要求时，应调用此工具，请注意：专业作图相关的请求（如流程图，序列图，统计图，甘特图，旅程图等）并不适用该函数，请使用其他函数解决。\"}\n{\"name\": \"generate_ppt\", \"description\": \"用于生成有明确主题ppt。若用户请求需要生成或润色ppt，且有明确的主题要求时，应调用此工具。\"}\n{\"name\": \"generate_mindmap\", \"description\": \"用于生成有明确主题思维导图。若用户请求需要生成或润色思维导图，且有明确的主题要求时，应调用此工具。\"}\n{\"name\": \"search_image\", \"description\": \"用于网络搜图。若用户请求需要搜索网络图片时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"搜索关键字。可包含多组关键词，关键词之间用空格区分，提取搜索主体。\"}}, \"required\": [\"query\"]}}\n</tools> \n\n# 环境信息\n- 今天的日期：2025年03月21日'''
    关闭搜索 =  '''# 工具信息\n你可以调用一个或多个工具来处理用户的请求，支持的工具签名如下:\n<tools>\n{\"name\": \"chat\", \"description\": \"用于普通问答。当用户请求不符合其他工具的要求时，应调用此工具。\"}\n{\"name\": \"url_fetch\", \"description\": \"用于提取超链接对应的网站信息。当用户请求包含超链接并希望对其提供的合法超链接进行信息提取时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"prompt\": {\"type\": \"string\", \"description\": \"该参数用于在多工具调用场景下，对用户请求中的超链接信息提取意图进行识别提取，确保能准确处理相关操作。\"}}}}\n{\"name\": \"generate_image\", \"description\": \"用于生成有明确主题的艺术类图片。若用户请求需要生成或润色艺术类，且有明确的主题要求时，应调用此工具，请注意：专业作图相关的请求（如流程图，序列图，统计图，甘特图，旅程图等）并不适用该函数，请使用其他函数解决。\"}\n{\"name\": \"generate_ppt\", \"description\": \"用于生成有明确主题ppt。若用户请求需要生成或润色ppt，且有明确的主题要求时，应调用此工具。\"}\n{\"name\": \"generate_mindmap\", \"description\": \"用于生成有明确主题思维导图。若用户请求需要生成或润色思维导图，且有明确的主题要求时，应调用此工具。\"}\n{\"name\": \"search_image\", \"description\": \"用于网络搜图。若用户请求需要搜索网络图片时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"搜索关键字。可包含多组关键词，关键词之间用空格区分，提取搜索主体。\"}}, \"required\": [\"query\"]}}\n</tools> \n\n# 环境信息\n- 今天的日期：2025年03月21日'''
    filter_typec = {"recommend", "websearch_result", "websearch", "url_fetch", "parsefile", "deepsearch_result"}
    chat_messages = []
    websearch_result = ""
    chat_messages.append(
        {"role": "system", "type": "text", "content": f'{打开搜索}'}
    )
    index =0
    urls = []
    for x in messages:
        if not x.get("role"):
            continue
        # if x.get("type") in ["websearch", "ppt_outline", "url_fetch"]:
        #     chat_messages.append(
        #         {"role": x.get("role"), "type": "execution", "content": x.get("content")}
        #     )

        if x.get("role") == "user" and x.get("type") == "text":
            q = qs[index] if index < len(qs) else ""
            index +=1
            content = x.get("content")
            file_ids = x.get("file_ids", [])
            if len(file_ids) > 0:              
                links = findall_filelinks(q)
                deeplinks = []
                for file_id in file_ids:
                    file_name = links.get(file_id,"")
                    deeplinks.append(
                        f"[{file_name}](wps365://files/{file_id})"
                    )
                content = " ".join(deeplinks) + content
            chat_messages.append(
                {"role": x.get("role"), "type": x.get("type"), "content": content}
            )
        elif x.get("role") == "assistant":
            typec = x.get("type")
            #code类型，无需处理直接转换
            if typec == "code" :
                chat_messages.append(
                    {"role": x.get("role"), "type": x.get("type"), "content": x.get("content")}
                )
                code_json = json.loads(x.get("content"))
                if code_json.get("function","") == "url_fetch":
                    urls = code_json.get("urls",[])
            # 保存文件和推荐保存：execution统一处理为{\"result\": \"ok\"}
            elif typec in {"docx_outline_file", "recommend_create","image"}:
                chat_messages.append(
                    {"role": x.get("role"), "type": "execution", "content": "{\"result\": \"ok\"}"}
                )
            #混存搜索结果
            elif typec in {"websearch_result", "deepsearch_result"}:
                websearch_result = x.get("content")
                print ("================================")
                print (websearch_result)
                print ("================================")
                
            #其他回复，当有搜索结果时拼接；其他不需要处理直接转换
            elif typec in {"text", "execution"}:
                if websearch_result:
                    try:
                        search_results = json.loads(websearch_result)
                        print("------------------")
                        print (search_results)
                        print("------------------")
                        if len(search_results) >= 3:
                            # 只取前3个条目进行拼接
                            formatted_results = "\n\n".join(f"[{item['title']}]({item['url']})" for item in search_results[:3])
                        else:
                            # 少于3个时全部拼接
                            formatted_results = "\n\n".join(f"[{item['title']}]({item['url']})" for item in search_results)
                        # formatted_results = "\n\n".join(f"[{item['title']}]({item['url']})" for item in search_results)
                        content = f"{formatted_results}\n{x.get('content')}"
                        print ("+++++++++++++++++++++++")
                        print (content)
                        print ("+++++++++++++++++++++++")
                        websearch_result = ""  # 清空 websearch_result
                    except json.JSONDecodeError:
                        # 如果解析失败，保留原始 websearch_result 内容
                        content = x.get("content")
                        websearch_result = ""  # 清空 websearch_result
                elif urls:
                    url_content_all = ""
                    for url in urls:
                        # url_content += "解析内容"
                        url_content = url_fetch(url)
                        # url_data = url_content.get("data",{})
                        url_xml = url_to_xml(url_content)
                        url_content_all = url_content_all + url_xml

                    content = f"网页内容：\n{url_content_all}\n总结内容：\n{x.get('content')}"
                    urls = []
                       
                else:
                    content = x.get("content")

                chat_messages.append(
                    {"role": x.get("role"), "type": "execution", "content": content}
                )
            elif typec in {"long_writer", "ppt_outline_text","mind_map","ppt_outline_text_v2"}:
                websearch_result = ""
                chat_messages.append(
                    {"role": x.get("role"), "type": "execution", "content": x.get("content")}
                )
            else : 
                pass
        else :
            pass
                    
    return chat_messages

def history_to_chat_messages(history: dict,qs: List[str]):
    all_messages = trans_chat_messages_2_messages(history.get("data", {}).get("list", []),qs)
    code_indexs = [i for i, x in enumerate(all_messages) if x.get("type") == "code"]
    result = {}
    user_counter = 1
    start_index = 0
    for i, x in enumerate(all_messages):
        if x.get("role") == "user":
            if start_index > 0 and result[str(start_index)]:
                #裁剪后再拼接
                # result[str(start_index)].append(all_messages[: i]) 
                result[str(start_index)].append(cutting_message(all_messages[: i])) 
                
            result[str(user_counter)] = []
            start_index = user_counter
            user_counter += 1
        if x.get("type") == "code":
            # result[str(start_index)].append(all_messages[: i]) 
            result[str(start_index)].append(cutting_message(all_messages[: i])) 
            print (x)
            print (result[str(start_index)])
    if start_index > 0 and all_messages:
        # result[str(start_index)].append(all_messages) 
        result[str(start_index)].append(cutting_message(all_messages))
    return result
    # return all_messages

def history_to_canvas_messages(history: dict,qs: List[str]):
    def cleanmessage(prompts):
        valid_params = {
            "chat": [],
            "websearch": ["query", "prompt", "query_tags", "extra_querys"],
            "generate_ppt": [],
            "generate_mindmap": [],
            "generate_image": [],
            "url" :[],
            "search_image": ["query"]
        }
    
        for k,v in prompts.items():
            for i,messages in enumerate(v):
                user_index = next((j for j, m in reversed(list(enumerate(messages))) if m["role"] == "user"), None)
                if user_index is not None:
                    messages[:] = [m for j, m in enumerate(messages) if not (j < user_index and m["role"] == "assistant" and m.get("type") == "code")]
                for m in messages:
                    if m["role"] == "assistant" and m["type"] == "code": 
                        code_data = json.loads(m["content"])  # 解析 JSON
                        function_name = code_data.get("function")
                        
                        if function_name in valid_params:
                            allowed_params = ["function"] + valid_params[function_name]  # 保留 function 字段
                            filtered_data = {k: v for k, v in code_data.items() if k in allowed_params}
                            
                            # 重新格式化 JSON，确保逗号和冒号后有空格
                            m["content"] = json.dumps(filtered_data, ensure_ascii=False, separators=(", ", ": "))
        return prompts

    def systemfilename(promptssp,file_names):
        # print (file_names)
        append_text = "\n#引用文件名\n" + "\n".join(file_names)
        print ("引用文件名拼接",append_text)
        for m in promptssp:
            if m["role"] == "system":
                m["content"] += append_text
        return promptssp
        
    all_messages = trans_chat_messages_2_messages(history.get("data", {}).get("list", []),qs)
    code_indexs = [i for i, x in enumerate(all_messages) if x.get("type") == "code"]
    result = {}
    user_counter = 1
    start_index = 0
    file_names = []
    for i, x in enumerate(all_messages):
        if x.get("role") == "user":
            if start_index > 0 and result[str(start_index)]:
                #裁剪后再拼接
                # result[str(start_index)].append(all_messages[: i]) 
                messageuser = cutting_message(copy.deepcopy(all_messages[: i]))
                
                if file_names :
                    messageuser = systemfilename(messageuser,file_names)
                    file_names = []
                    # filenamesp= True
                    # print ("文件名是否需要拼接",filenamesp)
                    print("清空文件名",file_names)
                result[str(start_index)].append(messageuser)  
                
            result[str(user_counter)] = []
            start_index = user_counter
            user_counter += 1

            file_names = re.findall(r"\[([^\]]+)\]\(wps365://files/[^\)]+\)", x.get("content")) or []
            
        if x.get("type") == "code":
            # result[str(start_index)].append(all_messages[: i]) 
            messagecode = cutting_message(copy.deepcopy(all_messages[: i]))
            if file_names:
                messagecode = systemfilename(messagecode,file_names)
            result[str(start_index)].append(messagecode) 

    if start_index > 0 and all_messages:
        messagelast = cutting_message(copy.deepcopy(all_messages))
        if file_names:
            messagelast = systemfilename(messagelast,file_names)
            # print ("文件名是否需要拼接",filenamesp)
        result[str(start_index)].append(messagelast)
        # result[str(start_index)].append(all_messages) 
        # result[str(start_index)].append(cutting_message(all_messages))

    resultcanvas = cleanmessage(result)
    return resultcanvas

# def history_to_pptmodel_messages(history: dict):
#     all_messages = history.get("data", {}).get("list", [])
#     result = {}
#     user_counter = 1
#     start_index = 0
#     for i, x in enumerate(all_messages):
#         if x.get("role") == "user":
#             result[str(user_counter)] = []
#             start_index = user_counter
#             user_counter += 1
#         if x.get("type") == "code" and json.loads(x.get("content")).get("function") == "generate_ppt":
#             model_message = history_to_model_messages(all_messages[: i])
#             if model_message:
#                 result[str(start_index)].append(model_message) 
#             # print (x)
#             print (result[str(start_index)])
#     return result

def history_to_model_messages(history: dict,fileinfo):
    messages = history.get("data", {}).get("list", [])
    new_messages = []
    last_upload_file_function = None
    user_content = None

    print ("拆分前:",fileinfo)
    if fileinfo.strip().startswith("问题"):
        # pattern = r"问题.*?内容\s*(.*?)(?=\s*问题|$)"
        pattern = r"(问题.*?内容[:：]?\s*)(.*?)(?=\s*问题|$)"
        matches = re.findall(pattern, fileinfo, re.DOTALL)
        split_fileinfo_cleaned = []
        for title, content in matches:
            cleaned_content = content.strip()
            split_fileinfo_cleaned.append(cleaned_content)
            # 从原始内容中移除已匹配的部分
            fileinfo = fileinfo.replace(title + content, "").strip()
        # 将提取的内容存入列表
        # split_fileinfo_cleaned = [match.strip() for match in matches]
    else:
        split_fileinfo_cleaned = [fileinfo.strip()]
    print ("拆分后:",split_fileinfo_cleaned)
    
    for message in messages:
        if message["type"] in["recommend","parsefile","help","url_fetch","recommend_create"]:
            continue
        if message["role"] == "user":
            user_content = message["content"]
            new_messages.append(
                    {"role": message.get("role"), "name": "用户", "content": message.get("content")}
                )
            print ("用户问题：",user_content)
        if message["type"] == "code":
            try:
                function_name = json.loads(message["content"]).get("function")
                print (function_name)
                # if function_name in ["url_fetch"]:
                if function_name in ["upload_files", "url_fetch"]:
                    if function_name == "upload_files":             
                        last_upload_file_function = "以下信息是文件和网页的解析结果，\n请参考解析的内容完成任务\n"+split_fileinfo_cleaned[0]+"{query}"
                        del split_fileinfo_cleaned[0]
                        content = last_upload_file_function.replace("{query}", user_content)
                        new_messages.pop()
                        new_messages.append(
                                {"role": "user", "name": "用户", "content": content}
                            )
                        new_messages.append(
                                {"role": message.get("role"), "name": "code", "content": message.get("content")}
                            )
                    if function_name == "url_fetch":
                        urls = json.loads(message["content"]).get("urls")
                        for url in urls:
                            user_content = user_content.replace(url, "").strip()
                        if user_content == "":
                            user_content = "解读这个网页"  
                        last_upload_file_function = "以下信息是文件和网页的解析结果，请参考解析的内容和图片完成任务\n### 网页内容摘要："+split_fileinfo_cleaned[0]+"\n{query}"
                        del split_fileinfo_cleaned[0]
                        content = last_upload_file_function.replace("{query}", user_content)
                        new_messages.pop()
                        new_messages.append(
                                {"role": "user", "name": "用户", "content": content}
                            )
                        new_messages.append(
                                {"role": message.get("role"), "name": "code", "content": message.get("content")}
                            )
                    # print("命中code：",last_upload_file_function)
                    
                elif function_name in ["chat","help","generate_ppt","code_interpreter","mindmap","image","websearch"]:
                    # if function_name == "websearch":
                    #     websearchquery = json.loads(message["content"]).get("query")
                    new_messages.append(
                    {"role": message.get("role"), "name": "code", "content": message.get("content")}
                )
            except json.JSONDecodeError:
                continue   
        if message["role"] == "assistant" and message["type"] == "websearch":
            message_content = json.loads(message["content"])
            websearchquery = message_content.get("search_queries") or message_content.get("query_tags") or message_content.get("query")

            # 如果是列表，则将其内容用逗号连接
            if isinstance(websearchquery, list):
                websearchquery = ", ".join(websearchquery)
            print ("搜索拆词",websearchquery)
            
        if message["role"] == "assistant" and message["type"] in {"websearch_result","deepsearch_result"} and websearchquery :
            # message_content = json.loads(content)
            websearchresult = webseatrchxml(json.loads(message["content"]))
            content = """以下信息是根据关键词"{websearchquery}"的搜索结果，请根据搜索结果完成任务\n{websearchresult}\n今天的日期是{modeltoday}。\n请回答问题""".replace("{websearchquery}",websearchquery).replace("{websearchresult}",websearchresult).replace("{modeltoday}",modeltoday)
            print ("新搜索content",content)
            for i in range(len(new_messages) - 1, -1, -1):  # 从倒数开始查找
                if new_messages[i]["role"] == "user":
                    new_messages[i]["content"] = content
                    break
            websearchquery = ""
            # new_messages.append(
            #         {"role": "user", "name": "用户", "content": message.get("content")}
            #     )
        elif message["role"] == "assistant" and message["type"] in {"image"}:
            new_messages.append({
                "role": message["role"],
                "name": "WPS 灵犀",
                "content": "{\"result\": \"ok\"}"
            })
         
        elif message["role"] == "assistant" and message["type"] in {"text", "execution","long_writer", "ppt_outline_text","mind_map","ppt_outline_text_v2"}:
            new_messages.append({
                "role": message["role"],
                "name": "WPS 灵犀",
                "content": message["content"]
            })
    
    return new_messages
    
def webseatrchxml(content):
    references = ET.Element("references")

# Loop through the first 3 elements of the content list
    for idx, item in enumerate(content, start=1):
        reference = ET.SubElement(references, "reference", index=str(idx))
        title = ET.SubElement(reference, "title")
        title.text = item["title"]
        content_elem = ET.SubElement(reference, "content")
        content_elem.text = item["summary"]
    
    # Convert the XML structure to a string
    xml_str = ET.tostring(references, encoding='utf-8', method='xml').decode('utf-8')
    
    

    # Prettify the XML output (optional)
    from xml.dom import minidom
    xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

    return xml_str

def url_to_xml(data):
    root = ET.Element("documents")
    try:
        json_data = json.loads(data)
        for info in json_data["data"]["res_infos"]:
            document = ET.SubElement(root, "document")
            ET.SubElement(document, "document_type").text = "网页"
            ET.SubElement(document, "document_name").text = info["metadata"]["title"]
            ET.SubElement(document, "document_url").text = info["url"]
            ET.SubElement(document, "document_content").text = info["content"]
        # print (root)
        xml_string = ET.tostring(root, encoding='utf-8').decode('utf-8')
        print(xml_string)

        return xml_string
    except json.JSONDecodeError:
        print ("prompt解析失败，直接跑工程接口")
        return ""
    

def get_user_question_answer(history: dict):
    # 输出结果
    output = []
    
    # 循环检查数据
    for item in history:
        if item['role'] == 'system':
            output.append(f"<|system|>\n    <|text|>{item['content']}<|endofblock|>\n<|endofmessage|>\n")
        
        elif item['role'] == 'user':
            output.append(f"<|user|>\n    <|text|>{item['content']}<|endofblock|>\n<|endofmessage|>\n")
        
        elif item['role'] == 'assistant':
            if item['type'] == 'code':
                output.append(f"<|assistant|>\n    <|code|>{item['content']}<|endofblock|>\n")
            
            elif item['type'] == 'text':
                if 'hits' in item:
                    hits = item['hits'] 
                    hits_output = []
                    for hit in hits:
                        hits_output.append(f"[{hit['title']}]({hit['url']})")
                    output.append(f"    <|execution|>" + "\n".join(hits_output) + f"\n{item['content']}" + f"\n<|endofmessage|>\n")
                else:
                    output.append(f"    <|execution|>{item['content']}\n<|endofmessage|>\n")
    # 打印结果
    final_output = "".join(output)
    print(final_output)


def cutting_message(messages):
    #裁剪消息，校验code格式
    for message in messages:
        if message.get("role", "") == "user":
            message["content"] = clip_message(message.get("content", ""))
        elif message.get("type", "") == "code":
            try:
                parsed_data = json.loads(message.get("content", ""))
                # 格式化 JSON 数据，确保冒号和逗号后带有一个空格
                formatted_json = json.dumps(parsed_data, ensure_ascii=False, separators=(", ", ": "))
                # 将 JSON 内容转义成字符串形式
                message["content"] = formatted_json.replace('"', '\"')
            except json.JSONDecodeError:
                print ("code解析失败")
        else:
            message["content"] = Cutter().reduce(message.get("content", ""))
    return messages
     
def chat_stream(messages: List[dict],chat_url = "", parameters = {"temperature": 0.01, "top_p": 0.01,"top_k":1}):
    contents = []
    final_output = ""
    content_type = None
    max_retries=3
    retry_delay=2
    attempts = 0
    
    # for message in messages:
    #     if message.get("role", "") == "user":
    #         message["content"] = clip_message(message.get("content", ""))
    #     else:
    #         message["content"] = Cutter().reduce(message.get("content", ""))

    new_history = keep_history(messages,max_tokens=16 * 1024)
    
    try:
        headers = {}
        body = {
            "logprobs": True,
            "top_logprobs": 1,
            "model": "copilot365",
            # "model" : "canvas",
            "stop": ["<|endofblock|>", "<|endofmessage|>"],
            "max_new_tokens": 4096,
            "temperature": parameters.get("temperature", 0.01),
            # "top_p": parameters.get("top_p", 0.01),
            # "top_k": parameters.get("top_k", 2),
            "messages": new_history,
            "stream": True,
        }
        # logger.info(f"request center model messages: {chat_messages}")
        while attempts < max_retries:
            try:
                resp = requests.post(chat_url, json=body, headers=headers, stream=True)
                resp.raise_for_status()
                print(f"Request body: {body}")
                break
            except Exception as e:
                attempts += 1
                print(f"call {chat_url} failed: {str(e)}")
                if attempts >= max_retries:
                    raise Exception("模型错误")
        stream = sseclient.SSEClient(resp)
        start_time = time.time()
        if resp.headers.get("Content-Type") == "application/json":
            return {"type": "error", "content": resp.text}

        for event in stream.events():
            # print(111,event)
            if event.data == "[DONE]":
                break
            data = json.loads(event.data)
            logging.info(f"event.data: {event.data}, data: {data}")
            # print(f"event.data: {event.data}, data: {data}")
            if not (data["status"] is None or data["status"]["code"] == 0):
                raise Exception(data["status"]["message"])

            choice = data["data"]["choices"][0]
            finish_reason = choice["finish_reason"]
            if finish_reason == "stop":
                break
            elif finish_reason == "length":
                raise Exception("达到最大生成长度")
            elif finish_reason == "sensitive":
                raise Exception("触发敏感词")
            elif finish_reason == "context":
                raise Exception("触发模型上下文长度限制")

            content_type = choice["type"]
            content = choice["delta"]
            contents.append(content)
            endofblock = True if finish_reason != "" else False
            if finish_reason != "":
                endofblock = True
    except Exception as e:
        print(f"chat_stream error: {str(e)}")
        contents.append(str(e))
    function = {"type": content_type, "content": "".join(contents)}
    return function


def chat_stream_logprob(messages: List[dict],chat_url = "", parameters = {"temperature": 0.01, "top_p": 0.01,"top_k":1}):
    contents = []
    res = {}
    final_output = ""
    res["logprobs"] = {} 
    res["logprobs"]["content"] = []
    content_type = None
    
    for message in messages:
        if message.get("role", "") == "user":
            message["content"] = clip_message(message.get("content", ""))
        else:
            message["content"] = Cutter().reduce(message.get("content", ""))

    new_history = keep_history(messages,max_tokens=16 * 1024)
    print ("===============裁剪后的消息体==================")
    print (new_history)
    print ("===============裁剪后的消息体==================")
    try:
        headers = {}
        body = {
            "logprobs": True,
            "top_logprobs": 1,
            "model": "copilot365",
            "stop": ["<|endofblock|>", "<|endofmessage|>"],
            "max_new_tokens": 4096,
            "temperature": parameters.get("temperature", 0.01),
            # "top_p": parameters.get("top_p", 0.01),
            # "top_k": parameters.get("top_k", 2),
            "messages": new_history,
            "stream": True,
        }
        # logger.info(f"request center model messages: {chat_messages}")
        try:
            resp = requests.post(chat_url, json=body, headers=headers, stream=True)
            # print (resp)
            resp.raise_for_status()
            print(f"Request body: {body}")
        except Exception as e:
            print(f"call {chat_url} failed: {str(e)}")
            raise Exception("模型错误")
        stream = sseclient.SSEClient(resp)
        start_time = time.time()
        if resp.headers.get("Content-Type") == "application/json":
            return {"type": "error", "content": resp.text}

        for event in stream.events():
            # print(111,event)
            if event.data == "[DONE]":
                break
            data = json.loads(event.data)
            logging.info(f"event.data: {event.data}, data: {data}")
            # print(f"event.data: {event.data}, data: {data}")
            if not (data["status"] is None or data["status"]["code"] == 0):
                raise Exception(data["status"]["message"])

            choice = data["data"]["choices"][0]
            logprobs = choice["logprobs"]["content"][0]
            if len(res["logprobs"]["content"]) < 8:
                res["logprobs"]["content"].append(logprobs)
            
            token = logprobs.get("token", "")
            # logprob_value = logprobs.get("logprob", "")
            logprob_value = log_to_decimal(logprobs.get("logprob", ""))
            formatted_entry = f'{{"token": "{token}", "logprob": {logprob_value}}}'
            final_output += formatted_entry + "\n"

            finish_reason = choice["finish_reason"]
            if finish_reason == "stop":
                break
            elif finish_reason == "length":
                raise Exception("达到最大生成长度")
            elif finish_reason == "sensitive":
                raise Exception("触发敏感词")
            elif finish_reason == "context":
                raise Exception("触发模型上下文长度限制")

            content_type = choice["type"]
            content = choice["delta"]
            contents.append(content)
            endofblock = True if finish_reason != "" else False
            if finish_reason != "":
                endofblock = True
    except Exception as e:
        print(f"chat_stream error: {str(e)}")
        # contents.append(str(e))
    res["message"] = {"role":"assistant","type":content_type,"content":"".join(contents)}
    # print (json.dumps(res,ensure_ascii=False,indent=4))
    confidences = get_output_confidence(res)
    print(json.dumps(confidences,ensure_ascii=False,indent=4))
    return confidences
    
def log_to_decimal(log_value):
    return math.pow(10, log_value)

def get_output_confidence(res: List[dict]):
    logprob = []
    function = {}
    try:
        logprob = res["logprobs"]["content"]
        f = res["message"]["content"].strip().strip("'")
        label_prob_token = str(logprob[0]["token"])
        label_prob = log_to_decimal(logprob[0]["logprob"])
        func_prob_token = str(json.loads(f)["function"])
        for lp in logprob:
            token = lp.get("token", "")
            if token in func_prob_token:
                func_prob = log_to_decimal(lp.get("logprob"))
                break
        confidences = {"label_prob_token": label_prob_token,"label_prob": label_prob,"func_prob_token": func_prob_token,"func_prob": func_prob}
    except Exception as e:
        print(f"An error occurred: {e}")
        confidences = {}
    return confidences

def clip_message(content: str, max_length: int = 2000) -> str:
    """裁剪消息，如果超过 max_length 则删去中间的用 ... 代替"""
    if len(content) <= max_length:
        return content
    logger.warning(
        f"content_length exceeds. max_length {max_length}. content: {content}"
    )
    half_length = max_length // 2
    return content[:half_length] + "..." + content[-half_length:]

    
def keep_history(history: List[Dict], max_tokens: int = 16 * 1024) -> List[Dict]:
    if len(history) == 0:
        return []

    rounds = []
    temp_round = {
        "messages": [],
        "length": 0
    }

    for chat_message in history:
        if chat_message["role"] == "user":
            if len(temp_round["messages"]) > 0:
                rounds.append(temp_round)
                temp_round = {
                    "messages": [chat_message],
                    "length": len(chat_message["content"].encode('utf-8'))
                }
                continue

        temp_round["messages"].append(chat_message)
        temp_round["length"] += len(chat_message["content"].encode('utf-8'))

    if len(temp_round["messages"]) > 0:
        rounds.append(temp_round)

    current_length = 0
    new_history = []
    for round in reversed(rounds):
        current_message = round["messages"].copy()
        current_message.extend(new_history)
        new_history = current_message
        current_length += round["length"]
        if current_length > max_tokens:
            break
    return new_history


if __name__ == '__main__':
    history = {
    "data": {
        "list": [
            {
                "collect_ids": [],
                "collections": None,
                "command": "",
                "comment_status": "",
                "content": "[扑热息痛市场分析.docx](wps365://files/ctIl0WsJaVm9)把以上文档转成PPT",
                "deep_searched": False,
                "favorite_id": "",
                "file_ids": [],
                "group_id": "530119549995983083",
                "is_favorite": False,
                "language": "zh-CN",
                "message_id": "530119550113423595",
                "reference_group_id": "",
                "role": "user",
                "style": "quick",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "{\"function\": \"upload_files\", \"files\": [\"ctIl0WsJaVm9\"], \"prompt\": \"提取核心要点\"}",
                "favorite_id": "",
                "group_id": "530119549995983083",
                "is_favorite": False,
                "message_id": "530119551388492011",
                "role": "assistant",
                "type": "code"
            },
            {
                "comment_status": "",
                "content": "[{\"result\": \"ok\", \"msg\": \"\", \"detail\": {}, \"file_id\": \"ctIl0WsJaVm9\", \"size\": 30801, \"name\": \"\\u6251\\u70ed\\u606f\\u75db\\u5e02\\u573a\\u5206\\u6790.docx\", \"read_length\": 5453, \"content_length\": 5453}]",
                "favorite_id": "",
                "group_id": "530119549995983083",
                "is_favorite": False,
                "message_id": "530119554475499755",
                "role": "assistant",
                "type": "parsefile"
            },
            {
                "comment_status": "",
                "content": "以下是《扑热息痛市场分析》的核心要点提取：\n\n1. 扑热息痛（Paracetamol）是一种疗效快、副作用较小的解热镇痛药，广泛应用于国际医药市场，是全球应用最广泛的药物之一。\n\n2. 全球扑热息痛年产量已达到7万余吨，主要生产商包括米林克劳特公司、龙·布朗公司、德国赫斯特公司下属的赛它套新公司等。这些公司具有生产规模大、技术先进、成本较低的优势。\n\n3. 在美国和欧洲的OTC（非处方药）市场上，扑热息痛是销售额最高的三种药物之一，其中美国是最大的市场。\n\n4. 中国和印度等国的扑热息痛生产发展迅速，在国际市场上占据了越来越多的份额。\n\n5. 中国从20世纪80年代末开始生产扑热息痛，近年来产量持续增长，已成为世界第二大原料药生产国。中国的扑热息痛主要出口到美国、德国、巴西等国家和地区。\n\n6. 我国扑热息痛的出口量自1993年以来大幅增长，但同时国内用量也保持了较高的增长速度。\n\n7. 我国扑热息痛生产存在规模小、工艺落后等问题，建议通过兼并与重组来优化产业结构，提高生产规模和技术水平。\n\n8. 我国医疗机构已经开始向患者提供药品价格清单，以提高价格透明度，改善医疗服务。\n\n9. 发展建议中提出，我国企业应提高扑热息痛的附加值，开发新产品，利用国内外市场潜力，同时淘汰副作用大的解热镇痛药品种。\n\n以上是根据文件内容整理的要点，涵盖了扑热息痛的全球市场地位、主要生产厂商、中美市场状况、中国产量增长及出口情况、发展挑战及建议等核心信息。",
                "favorite_id": "",
                "group_id": "530119549995983083",
                "is_favorite": False,
                "message_id": "530119554475565291",
                "role": "assistant",
                "type": "execution"
            },
            {
                "comment_status": "",
                "content": "{\"function\": \"generate_ppt\"}",
                "favorite_id": "",
                "group_id": "530119549995983083",
                "is_favorite": False,
                "message_id": "530119569944223979",
                "role": "assistant",
                "type": "code"
            },
            {
                "comment_status": "",
                "content": "主题：扑热息痛市场分析\n\n# 扑热息痛概述\n## 扑热息痛的定义与应用\n### 解热镇痛药的定义\n* 扑热息痛（对乙酰氨基酚）是一种疗效快、副作用较小的解热镇痛药，广泛应用于国际医药市场。\n### 全球应用情况\n* 扑热息痛是全球应用最广泛的药物之一，尤其在国际医药市场上占据重要地位。\n\n## 扑热息痛的全球市场\n### 主要生产厂商\n* 全球扑热息痛年产量已达到7万余吨，主要生产商包括米林克劳特公司、龙·布朗公司等。\n### 美国和欧洲市场\n* 在美国和欧洲的OTC市场上，扑热息痛是销售额最高的三种药物之一，其中美国是最大的市场。\n\n# 中国扑热息痛市场分析\n## 中国市场的历史与现状\n### 中国扑热息痛的生产历史\n* 中国从20世纪80年代末开始生产扑热息痛，近年来产量持续增长。\n### 中国扑热息痛的出口与内销\n* 中国的扑热息痛主要出口到美国、德国等国家和地区，同时国内用量也保持了较高的增长速度。\n\n## 中国扑热息痛的发展挑战与建议\n### 生产规模与技术问题\n* 我国扑热息痛生产存在规模小、工艺落后等问题，建议通过兼并与重组来优化产业结构。\n### 发展建议\n* 提高扑热息痛的附加值，开发新产品，利用国内外市场潜力，同时淘汰副作用大的解热镇痛药品种。\n\n# 扑热息痛的未来展望\n## 市场增长趋势\n### 国内外市场增长情况\n* 无论是西方发达国家还是发展中国家，扑热息痛制剂的市场销售额一直呈稳定增长的态势。\n## 医疗机构药品价格透明化\n### 药品价格清单的提供\n* 我国医疗机构已经开始向患者提供药品价格清单，以提高价格透明度，改善医疗服务。",
                "favorite_id": "",
                "group_id": "530119549995983083",
                "is_favorite": False,
                "message_id": "530119569944289515",
                "role": "assistant",
                "type": "ppt_outline_text"
            },
            {
                "comment_status": "",
                "content": "[\"如何将文档内容转换成PPT的步骤?\", \"扑热息痛在发展中国家的市场表现如何?\", \"中国扑热息痛出口的主要国家有哪些?\"]",
                "favorite_id": "",
                "group_id": "530119549995983083",
                "is_favorite": False,
                "message_id": "530119594673774827",
                "role": "assistant",
                "type": "recommend"
            }
        ]
    },
    "result": "ok"
}

    new_code_message= history_to_pptmodel_messages(history)
    prompt = json.dumps(new_code_message,ensure_ascii=False,indent=2)
    print (prompt)
    
    his = {
    "data": {
        "list": [
            {
                "comment_status": "",
                "content": "最近有没有放弃农村宅基地的相关政策",
                "file_ids": ["111","222"],
                "group_id": "524645837901416117",
                "is_favorite": False,
                "message_id": "524645837918193333",
                "role": "user",
                "show_content": "",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "{\"function\": \"websearch\", \"query\": \"最近 放弃 农村宅地 相关政策\", \"prompt\": \"根据\\\"最近 放弃 农村宅地 相关政策\\\"的搜索结果,回答最近是否有放弃农村宅基地的相关政策\", \"query_tag\": [\"政策\", \"农业\", \"房产\"], \"recency_days\": 30}",
                "file_ids": None,
                "group_id": "524645837901416117",
                "is_favorite": False,
                "message_id": "524645838018922165",
                "role": "assistant",
                "show_content": "",
                "type": "code"
            },
            {
                "comment_status": "",
                "content": "[{\"title\": \"多地出台鼓励放弃、退出农村宅基地相关政策_购房_发展_给予\", \"url\": \"https://m.sohu.com/coo/sg/789863719_121731890\", \"summary\": \"\"}, {\"title\": \"近日,多地出台了鼓励农村居民放弃宅基地进城购房的政策.安徽省凤阳县给予5万元购房奖励,江苏省南通市自2024年4月1日至2025年6月30日期间购买...\", \"url\": \"https://www.douyin.com/video/7386125421676350735\", \"summary\": \"\"}, {\"title\": \"农村放弃宅基地补助政策 - 抖音\", \"url\": \"https://www.douyin.com/zhuanti/7386527449690966068\", \"summary\": \"\"}, {\"title\": \"新政策来了!鼓励放弃农村宅基地进城买房,这些你要知道_房产资讯_房天下\", \"url\": \"https://nt.news.fang.com/open/50522997.html\", \"summary\": \"\"}, {\"title\": \"农村宅基地确权_退出_补偿新政策 - 土流网\", \"url\": \"https://m.tuliu.com/tags/1268.html\", \"summary\": \"\"}, {\"title\": \"为救房地产又出新招:多地鼓励放弃、退出农村宅基-今日头条\", \"url\": \"https://m.toutiao.com/video/7386214093969195535/?upstream_biz=toutiao_pc\", \"summary\": \"\"}, {\"title\": \"鼓励农民自愿放弃宅基地,释放了什么信号?|买房|购房|房地产|土地财政|农村宅基地_网易订阅\", \"url\": \"https://3g.163.com/dy/article_v2/J5PNFA6N0535PKJN.html\", \"summary\": \"\"}, {\"title\": \"多地鼓励农民放弃农村宅基地,退出宅基地补偿多少钱?怎么申请?_进行_购房_发展\", \"url\": \"https://m.sohu.com/coo/sg/789217359_121778026\", \"summary\": \"\"}]",
                "group_id": "524645837901416117",
                "message_id": "524645841374365365",
                "role": "assistant",
                "type": "websearch_result"
            },
            {
                "comment_status": "",
                "content": "**最近有鼓励放弃农村宅基地的政策**：根据提供的搜索结果，多地出台了鼓励农村居民放弃宅基地进城购房的政策。例如，安徽省凤阳县给予5万元购房奖励，江苏省南通市在特定时间段内购买房产的农村居民也有相应的政策支持[^2][^4]。这些政策旨在鼓励农民自愿放弃宅基地，以促进房地产市场的发展和土地资源的合理利用[^7]。此外，还有关于宅基地确权、退出和补偿的新政策，这些政策为农民放弃宅基地提供了具体的指导和补偿措施[^5]。",
                "group_id": "524645837901416117",
                "hits": [
                    {
                        "summary": "",
                        "title": "多地出台鼓励放弃、退出农村宅基地相关政策_购房_发展_给予",
                        "url": "https://m.sohu.com/coo/sg/789863719_121731890"
                    },
                    {
                        "summary": "",
                        "title": "近日,多地出台了鼓励农村居民放弃宅基地进城购房的政策.安徽省凤阳县给予5万元购房奖励,江苏省南通市自2024年4月1日至2025年6月30日期间购买...",
                        "url": "https://www.douyin.com/video/7386125421676350735"
                    },
                    {
                        "summary": "",
                        "title": "农村放弃宅基地补助政策 - 抖音",
                        "url": "https://www.douyin.com/zhuanti/7386527449690966068"
                    },
                    {
                        "summary": "",
                        "title": "新政策来了!鼓励放弃农村宅基地进城买房,这些你要知道_房产资讯_房天下",
                        "url": "https://nt.news.fang.com/open/50522997.html"
                    },
                    {
                        "summary": "",
                        "title": "农村宅基地确权_退出_补偿新政策 - 土流网",
                        "url": "https://m.tuliu.com/tags/1268.html"
                    },
                    {
                        "summary": "",
                        "title": "为救房地产又出新招:多地鼓励放弃、退出农村宅基-今日头条",
                        "url": "https://m.toutiao.com/video/7386214093969195535/?upstream_biz=toutiao_pc"
                    },
                    {
                        "summary": "",
                        "title": "鼓励农民自愿放弃宅基地,释放了什么信号?|买房|购房|房地产|土地财政|农村宅基地_网易订阅",
                        "url": "https://3g.163.com/dy/article_v2/J5PNFA6N0535PKJN.html"
                    },
                    {
                        "summary": "",
                        "title": "多地鼓励农民放弃农村宅基地,退出宅基地补偿多少钱?怎么申请?_进行_购房_发展",
                        "url": "https://m.sohu.com/coo/sg/789217359_121778026"
                    }
                ],
                "message_id": "524645841374365365",
                "role": "assistant",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "放弃太亏了吧，自建房住的还是很舒服的",
                "file_ids": [],
                "group_id": "524645849595130312",
                "is_favorite": False,
                "message_id": "524645849612104136",
                "role": "user",
                "show_content": "",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "{\"function\": \"chat\"}",
                "file_ids": None,
                "group_id": "524645849595130312",
                "is_favorite": False,
                "message_id": "524645849964294600",
                "role": "assistant",
                "show_content": "",
                "type": "code"
            },
            {
                "comment_status": "",
                "content": "放弃农村宅基地确实是一个需要慎重考虑的决定，因为这涉及到多方面的利益和情感因素。自建房通常具有以下优点：\n\n1. **成本优势**：自建房的成本通常低于城市购买商品房的成本，尤其是在农村地区，土地成本较低，建材和人工费用也相对较低。\n\n2. **空间自由**：自建房可以根据个人需求和喜好设计房屋的大小、布局和风格，拥有更大的空间自由度。\n\n3. **环境舒适**：农村环境通常较为宁静，空气质量好，生活节奏较慢，适合追求自然和宁静生活的人群。\n\n4. **社区联系**：农村社区通常具有较强的邻里联系和社区凝聚力，居民之间相互帮助，形成紧密的社区关系。\n\n然而，放弃宅基地进城购房也有其吸引力，例如：\n\n1. **城市便利**：城市提供了更多的就业机会、教育资源、医疗设施和娱乐活动。\n\n2. **生活品质**：城市生活品质通常较高，有更多现代化的设施和服务。\n\n3. **投资价值**：城市房产通常具有较高的保值和增值潜力。\n\n4. **政策激励**：如前所述，一些地方政府为了促进城市化和土地资源的合理利用，提供了购房奖励等激励措施。\n\n最终是否放弃宅基地，需要根据个人的实际情况、家庭需求、长远规划以及对农村和城市生活的偏好来综合考虑。同时，也要关注相关政策的变化，以便做出最符合自身利益的决策。在做出决定之前，建议咨询专业人士，了解详细的政策内容和可能的法律后果。",
                "file_ids": None,
                "group_id": "524645849595130312",
                "is_favorite": False,
                "message_id": "524645850266284488",
                "role": "assistant",
                "show_content": "",
                "type": "execution"
            },
            {
                "comment_status": "",
                "content": [
                    "自建房在设计上有哪些自由度?",
                    "城市房产的保值增值潜力如何?",
                    "放弃宅基地进城购房有哪些政策激励?"
                ],
                "group_id": "524645849595130312",
                "is_favorite": False,
                "message_id": "524645859997069768",
                "type": "recommend"
            },
            {
                "comment_status": "",
                "content": "农村宅基地能个人转卖给个人吗",
                "file_ids": [],
                "group_id": "524645863369224648",
                "is_favorite": False,
                "message_id": "524645863386067400",
                "role": "user",
                "show_content": "",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "{\"function\": \"chat\"}",
                "file_ids": None,
                "group_id": "524645863369224648",
                "is_favorite": False,
                "message_id": "524645864090710472",
                "role": "assistant",
                "show_content": "",
                "type": "code"
            },
            {
                "comment_status": "",
                "content": "在中国，农村宅基地的转让受到严格的法律限制。根据中国现行的《土地管理法》和相关政策，农村宅基地的所有权属于农村集体经济组织，农民只有使用权。宅基地使用权不得随意转让，尤其是不得转让给非本集体经济组织的成员。\n\n具体来说，农村宅基地的转让通常需要满足以下条件：\n\n1. **转让对象**：宅基地使用权的转让通常只能在本集体经济组织内部进行，即只能转让给本村的其他村民。\n\n2. **审批程序**：转让宅基地使用权需要经过集体经济组织的同意，并报请乡镇人民政府批准。\n\n3. **用途限制**：转让后的宅基地仍然只能用于建设住宅，不能用于商业开发等其他用途。\n\n4. **政策变化**：政策可能会有所调整，因此在考虑转让宅基地之前，应当咨询当地土地管理部门，了解最新的政策规定。\n\n如果个人想要将宅基地转让给非本集体经济组织的成员，这通常是不被允许的。不过，随着中国农村土地制度改革的推进，一些地区可能会有试点政策允许宅基地使用权的流转，但这需要根据具体地区的政策来确定。\n\n因此，如果您考虑转让农村宅基地，建议先咨询当地的土地管理部门或法律专业人士，以确保符合法律规定，避免违法行为。同时，也要注意保护自己的合法权益，避免因不了解政策而遭受损失。",
                "file_ids": None,
                "group_id": "524645863369224648",
                "is_favorite": False,
                "message_id": "524645864409477576",
                "role": "assistant",
                "show_content": "",
                "type": "execution"
            },
            {
                "comment_status": "",
                "content": [
                    "宅基地转让需要哪些审批程序?",
                    "宅基地转让后能否用于商业开发?",
                    "如何了解最新的宅基地政策规定?"
                ],
                "group_id": "524645863369224648",
                "is_favorite": False,
                "message_id": "524645873620169160",
                "type": "recommend"
            },
            {
                "comment_status": "",
                "content": "自愿放弃农村宅基地是什么时候的政策",
                "file_ids": [],
                "group_id": "524645877092987336",
                "is_favorite": False,
                "message_id": "524645877110354376",
                "role": "user",
                "show_content": "",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "{\"function\": \"websearch\", \"query\": \"自愿放弃 农村宅基地 政策 时间\", \"prompt\": \"根据\\\"自愿放弃 农村宅基地 政策 时间\\\"的搜索结果,回答自愿放弃农村宅集团地的政策是什么时候\", \"query_tag\": [\"政策\", \"农业\", \"房产\"], \"recency_days\": 0}",
                "file_ids": None,
                "group_id": "524645877092987336",
                "is_favorite": False,
                "message_id": "524645878200349128",
                "role": "assistant",
                "show_content": "",
                "type": "code"
            },
            {
                "comment_status": "",
                "content": "[{\"title\": \"6月起,鼓励放弃、退出农村宅基地!一次性给予5万元购房奖励!多地出台相关政策_住房_房地产市场_商品\", \"url\": \"https://m.sohu.com/coo/sg/788456155_121119269\", \"summary\": \"\"}, {\"title\": \"下月起,进城落户村民可依法自愿有偿退出宅基地_农村\", \"url\": \"https://m.sohu.com/coo/sg/483084291_260616\", \"summary\": \"\"}, {\"title\": \"公开信件内容页_书记县长信箱_泸县政府网站\", \"url\": \"http://www.luxian.gov.cn/petition/220\", \"summary\": \"领导,您好!我想咨询农户自愿放弃农村宅基地的政策.因为我家情况特殊,我是属于寄养,但家里父亲5年前已过世,我自己的户口上大学迁出后回迁到方洞镇街村.政府现在有宅基地回收政策,我这样的情况是按照什么标准执行的?请帮忙确认下,谢谢 农民合法取得的宅基地,拆除房屋补偿标准为:砖混及以上结构450元/平方米、砖瓦结构380元/平方米、土瓦及以下结构300元/平方米;超占面积或“一户多宅”的,拆除房屋补助标准为:砖混及以上结构100元/平方米、砖瓦结构80元/平方米、土瓦及以下结构60元/平方米.宅基地占地面积外建设用地面积拆除复耕,按复耕验收合格面积扣除房屋占地面积后给予20元/平方米的补助 \"}, {\"title\": \"多地出台鼓励退出农村宅基地 多地设奖励促宅基地退出_新闻频道_中华网\", \"url\": \"https://3g.china.com/act/news/10000169/20240624/46741208.html\", \"summary\": \"\"}, {\"title\": \"明确了,中央定调:鼓励村民放弃宅基地,农民朋友该何去何从?|买房|购房|农村宅基地_网易订阅\", \"url\": \"https://3g.163.com/dy/article_v2/J5F05Q390552LSYM.html\", \"summary\": \"\"}, {\"title\": \"鼓励放弃、退出农村宅基地!江苏、安徽等地出台相关政策\", \"url\": \"https://news.ycwb.com/2024-06/23/content_52763525.htm\", \"summary\": \"\"}, {\"title\": \"好消息!鼓励农民自愿放弃宅基地,一次性补贴5万,比下岗工人强|买房|购房|农村宅基地_网易订阅\", \"url\": \"https://3g.163.com/dy/article_v2/J5DFCJI605566UIE.html\", \"summary\": \"\"}, {\"title\": \"要我自愿放弃宅基地是什么意思是什么意思_2024年宅基地还能盖房吗_多特软件资讯\", \"url\": \"https://news.duote.com/m/202406/594527.html\", \"summary\": \"\"}, {\"title\": \"鼓励放弃、退出农村宅基地!江苏、安徽、湖北等地出台相关政策-今日头条\", \"url\": \"https://m.toutiao.com/video/7384051445706588723/?upstream_biz=toutiao_pc\", \"summary\": \"\"}, {\"title\": \"农村宅基地确权_退出_补偿新政策 - 土流网\", \"url\": \"https://m.tuliu.com/tags/1268.html\", \"summary\": \"\"}]",
                "group_id": "524645877092987336",
                "message_id": "524645881572569544",
                "role": "assistant",
                "type": "websearch_result"
            },
            {
                "comment_status": "",
                "content": "**自愿放弃农村宅基地的政策时间**：根据提供的搜索结果，多地出台了鼓励村民自愿放弃宅基地的政策，具体政策实施的时间点在2024年6月起[^1][^4][^6][^7][^9]。这些政策旨在鼓励进城落户的村民依法自愿有偿退出宅基地，并提供了一次性购房奖励，如一次性给予5万元购房奖励[^1][^7]。此外，还明确了宅基地的补偿标准，包括拆除房屋的补偿和超占面积或“一户多宅”的补助标准[^3]。这些政策的出台是为了促进农村宅基地的合理利用和农村土地资源的优化配置。",
                "group_id": "524645877092987336",
                "hits": [
                    {
                        "summary": "",
                        "title": "6月起,鼓励放弃、退出农村宅基地!一次性给予5万元购房奖励!多地出台相关政策_住房_房地产市场_商品",
                        "url": "https://m.sohu.com/coo/sg/788456155_121119269"
                    },
                    {
                        "summary": "",
                        "title": "下月起,进城落户村民可依法自愿有偿退出宅基地_农村",
                        "url": "https://m.sohu.com/coo/sg/483084291_260616"
                    },
                    {
                        "summary": "领导,您好!我想咨询农户自愿放弃农村宅基地的政策.因为我家情况特殊,我是属于寄养,但家里父亲5年前已过世,我自己的户口上大学迁出后回迁到方洞镇街村.政府现在有宅基地回收政策,我这样的情况是按照什么标准执行的?请帮忙确认下,谢谢 农民合法取得的宅基地,拆除房屋补偿标准为:砖混及以上结构450元/平方米、砖瓦结构380元/平方米、土瓦及以下结构300元/平方米;超占面积或“一户多宅”的,拆除房屋补助标准为:砖混及以上结构100元/平方米、砖瓦结构80元/平方米、土瓦及以下结构60元/平方米.宅基地占地面积外建设用地面积拆除复耕,按复耕验收合格面积扣除房屋占地面积后给予20元/平方米的补助 ",
                        "title": "公开信件内容页_书记县长信箱_泸县政府网站",
                        "url": "http://www.luxian.gov.cn/petition/220"
                    },
                    {
                        "summary": "",
                        "title": "多地出台鼓励退出农村宅基地 多地设奖励促宅基地退出_新闻频道_中华网",
                        "url": "https://3g.china.com/act/news/10000169/20240624/46741208.html"
                    },
                    {
                        "summary": "",
                        "title": "明确了,中央定调:鼓励村民放弃宅基地,农民朋友该何去何从?|买房|购房|农村宅基地_网易订阅",
                        "url": "https://3g.163.com/dy/article_v2/J5F05Q390552LSYM.html"
                    },
                    {
                        "summary": "",
                        "title": "鼓励放弃、退出农村宅基地!江苏、安徽等地出台相关政策",
                        "url": "https://news.ycwb.com/2024-06/23/content_52763525.htm"
                    },
                    {
                        "summary": "",
                        "title": "好消息!鼓励农民自愿放弃宅基地,一次性补贴5万,比下岗工人强|买房|购房|农村宅基地_网易订阅",
                        "url": "https://3g.163.com/dy/article_v2/J5DFCJI605566UIE.html"
                    },
                    {
                        "summary": "",
                        "title": "要我自愿放弃宅基地是什么意思是什么意思_2024年宅基地还能盖房吗_多特软件资讯",
                        "url": "https://news.duote.com/m/202406/594527.html"
                    },
                    {
                        "summary": "",
                        "title": "鼓励放弃、退出农村宅基地!江苏、安徽、湖北等地出台相关政策-今日头条",
                        "url": "https://m.toutiao.com/video/7384051445706588723/?upstream_biz=toutiao_pc"
                    },
                    {
                        "summary": "",
                        "title": "农村宅基地确权_退出_补偿新政策 - 土流网",
                        "url": "https://m.tuliu.com/tags/1268.html"
                    }
                ],
                "message_id": "524645881572569544",
                "role": "assistant",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "广东省还没有出相关政策么",
                "file_ids": [],
                "group_id": "524645890497982920",
                "is_favorite": False,
                "message_id": "524645890515546568",
                "role": "user",
                "show_content": "",
                "type": "text"
            },
            {
                "comment_status": "",
                "content": "{\"function\": \"websearch\", \"query\": \"2024年 广东省 鼓励 村民 放弃 农村宅 政策\", \"prompt\": \"根据\\\"2024年 广东省 鼓励 村民 放弃 农村宅 政策\\\"的搜索结果,回答广东省还没有出相关政策\", \"query_tag\": [\"政策\", \"农业\", \"房产\"]}",
                "file_ids": None,
                "group_id": "524645890497982920",
                "is_favorite": False,
                "message_id": "524645891840225736",
                "role": "assistant",
                "show_content": "",
                "type": "code"
            },
            {
                "comment_status": "",
                "content": "[{\"title\": \"多地出台鼓励放弃农村宅基地政策_闻海泛舟_2024年06月24日_微头条-今日头条\", \"url\": \"https://m.toutiao.com/w/1802693169333251/\", \"summary\": \"\"}, {\"title\": \"多地发文鼓励农村居民放弃宅基地进城买房-广州搜狐焦点\", \"url\": \"https://gsgsh.focus.cn/gz/zixun/2781e41bb50c4f5f.html\", \"summary\": \"\"}, {\"title\": \"多地鼓励退出农村宅基地,三农专家温铁军:趁有钱,赶紧买地建房-今日头条\", \"url\": \"https://m.toutiao.com/video/7385047461419434511/?upstream_biz=toutiao_pc\", \"summary\": \"\"}, {\"title\": \"南方农村报新闻:退出宅基地 奖励5万元-2024年06月27日\", \"url\": \"https://epaper.nfncb.cn/nfnc/content/20240627/Articel04002MT.htm\", \"summary\": \"\"}, {\"title\": \"2024鼓励农村居民放弃宅基地的措施有哪些? -宅基地及房屋- 土流网\", \"url\": \"https://m.tuliu.com/wnews/read-152914.html\", \"summary\": \"\"}, {\"title\": \"楼市重磅,多地出台鼓励放弃农村宅基地进城购房政策,给5万奖励-今日头条\", \"url\": \"https://m.toutiao.com/video/7383619986588090906/?upstream_biz=toutiao_pc\", \"summary\": \"\"}, {\"title\": \"农民有福气了!多地出台鼓励放弃退出宅基地政策,进城买房有补贴-今日头条\", \"url\": \"https://m.toutiao.com/video/7383669524493353511/?upstream_biz=toutiao_pc\", \"summary\": \"\"}, {\"title\": \"2024鼓励农村居民放弃宅基地的措施有哪些?你支持哪种?_哔哩哔哩_bilibili\", \"url\": \"https://m.bilibili.com/video/BV1Jz421z7Kt/\", \"summary\": \"未经作者授权,禁止转载 投币 My Soul 1.0万 0 展开\"}, {\"title\": \"“鼓励农民放弃宅基地进城买房”背后:有偿退出已试点多年 专家称保障比奖励更有用|承包地|农村宅基地_网易订阅\", \"url\": \"https://3g.163.com/dy/article_v2/J5KDRI8U051492T3.html\", \"summary\": \"\"}, {\"title\": \"鼓励农民放弃宅基地进城买房有奖励?网友炸锅不买账-今日头条\", \"url\": \"https://m.toutiao.com/video/7383852344569496075/?upstream_biz=toutiao_pc\", \"summary\": \"\"}]",
                "group_id": "524645890497982920",
                "message_id": "524645895279555016",
                "role": "assistant",
                "type": "websearch_result"
            },
            {
                "comment_status": "",
                "content": "**广东省尚未出台相关政策**：根据提供的搜索结果摘要，目前没有明确的信息表明广东省已经出台了鼓励村民放弃农村宅基地的政策。搜索结果中提到的政策多为其他地区的情况，例如多地出台鼓励政策、奖励措施等，但并未提及广东省的具体情况[^1][^2][^3][^4][^5][^6][^7][^8][^9][^10]。因此，可以得出结论，截至2024年7月29日，广东省还没有出相关政策。",
                "group_id": "524645890497982920",
                "hits": [
                    {
                        "summary": "",
                        "title": "多地出台鼓励放弃农村宅基地政策_闻海泛舟_2024年06月24日_微头条-今日头条",
                        "url": "https://m.toutiao.com/w/1802693169333251/"
                    },
                    {
                        "summary": "",
                        "title": "多地发文鼓励农村居民放弃宅基地进城买房-广州搜狐焦点",
                        "url": "https://gsgsh.focus.cn/gz/zixun/2781e41bb50c4f5f.html"
                    },
                    {
                        "summary": "",
                        "title": "多地鼓励退出农村宅基地,三农专家温铁军:趁有钱,赶紧买地建房-今日头条",
                        "url": "https://m.toutiao.com/video/7385047461419434511/?upstream_biz=toutiao_pc"
                    },
                    {
                        "summary": "",
                        "title": "南方农村报新闻:退出宅基地 奖励5万元-2024年06月27日",
                        "url": "https://epaper.nfncb.cn/nfnc/content/20240627/Articel04002MT.htm"
                    },
                    {
                        "summary": "",
                        "title": "2024鼓励农村居民放弃宅基地的措施有哪些? -宅基地及房屋- 土流网",
                        "url": "https://m.tuliu.com/wnews/read-152914.html"
                    },
                    {
                        "summary": "",
                        "title": "楼市重磅,多地出台鼓励放弃农村宅基地进城购房政策,给5万奖励-今日头条",
                        "url": "https://m.toutiao.com/video/7383619986588090906/?upstream_biz=toutiao_pc"
                    },
                    {
                        "summary": "",
                        "title": "农民有福气了!多地出台鼓励放弃退出宅基地政策,进城买房有补贴-今日头条",
                        "url": "https://m.toutiao.com/video/7383669524493353511/?upstream_biz=toutiao_pc"
                    },
                    {
                        "summary": "未经作者授权,禁止转载 投币 My Soul 1.0万 0 展开",
                        "title": "2024鼓励农村居民放弃宅基地的措施有哪些?你支持哪种?_哔哩哔哩_bilibili",
                        "url": "https://m.bilibili.com/video/BV1Jz421z7Kt/"
                    },
                    {
                        "summary": "",
                        "title": "“鼓励农民放弃宅基地进城买房”背后:有偿退出已试点多年 专家称保障比奖励更有用|承包地|农村宅基地_网易订阅",
                        "url": "https://3g.163.com/dy/article_v2/J5KDRI8U051492T3.html"
                    },
                    {
                        "summary": "",
                        "title": "鼓励农民放弃宅基地进城买房有奖励?网友炸锅不买账-今日头条",
                        "url": "https://m.toutiao.com/video/7383852344569496075/?upstream_biz=toutiao_pc"
                    }
                ],
                "message_id": "524645895279555016",
                "role": "assistant",
                "type": "text"
            }
        ],
        "total": 17
    },
    "result": "ok"
}
    # messages = history_to_chat_messages(his,qs=["[小黄的简历.docx](wps365://files/111) [小王的简历.docx](wps365://files/222)","","","",""])
    
    
    # print(messages[0])
    

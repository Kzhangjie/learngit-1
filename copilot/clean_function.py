from types import MethodType
from run_batch.run_ai import RunAi
import re

file_id = "cgGYXWX5SZzL"
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
from gen_prompt import convert_messages_for_gpt,extra_codes,extra_codes_from_logs
from copilot.code_session import history_to_chat_messages,trans_chat_messages_2_messages
from api2 import Copilot
cc = Copilot(is_test=True,model_url="",custom_headers={},search_engines="")
# cc = Copilot(is_test=False,model_url="",custom_headers={},search_engines="")
def run_one(self,row):
    try:
        row_index = row["row_index"]
        prompts = json.loads(row["prompts"] +row.get("prompts1","")+row.get("prompts2","")+row.get("prompts3",""))

        #删除参数
        for k,v in prompts.items():
            for i,messages in enumerate(v):
                user_index = next((j for j, m in reversed(list(enumerate(messages))) if m["role"] == "user"), None)
                if user_index is not None:
                    messages[:] = [m for j, m in enumerate(messages) if not (j < user_index and m["role"] == "assistant" and m.get("type") == "code")]
                for m in messages:
                    if m["role"] == "system":
                        m["content"] = "# 工具信息\n你可以调用一个或多个工具来处理用户的请求，支持的工具签名如下:\n<tools>\n{\"name\": \"chat\", \"description\": \"用于普通问答。当用户请求不符合其他工具的要求时，应调用此工具。\"}\n{\"name\": \"websearch\", \"description\": \"用于信息检索。若用户请求需要获取实时、最新信息、人设信息时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"搜索关键字。可包含多组关键词，关键词之间用空格区分；如需获取特定时效性信息，需在关键词中加上相应时间范围；如请求涉及人设信息提问时，使用“WPS灵犀”指代你。\"}, \"prompt\": {\"type\": \"string\", \"description\": \"该参数用于在多工具调用场景下，对用户请求中的搜索意图进行识别提取，确保能准确处理相关操作。\"}, \"extra_querys\": {\"type\": \"array\", \"description\": \"若用户请求过于复杂，需要多次搜索保证回答效果时，使用该参数进行描述。\", \"items\": {\"type\": \"string\", \"description\": \"多次搜索关键字。\"}}, \"query_tags\": {\"type\": \"array\", \"description\": \"搜索标签，用户请求与WPS组件能力或人设信息相关时，应使用此参数标识。\", \"items\": {\"type\": \"string\", \"description\": \"询问与wps组件能力相关信息时，使用“wps”标签，与人设信息相关时，使用“人设”标签。\", \"enum\": [\"wps\", \"人设\"]}}, \"deep_search\": {\"type\": \"bool\", \"description\": \"若用户请求希望对问题进行深度剖析时，该参数为true。\"}}, \"required\": [\"query\"]}}\n{\"name\": \"url_fetch\", \"description\": \"用于提取超链接对应的网站信息。当用户请求包含超链接并希望对其提供的合法超链接进行信息提取时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"prompt\": {\"type\": \"string\", \"description\": \"该参数用于在多工具调用场景下，对用户请求中的超链接信息提取意图进行识别提取，确保能准确处理相关操作。\"}}}}\n{\"name\": \"generate_image\", \"description\": \"用于生成有明确主题的艺术类图片。若用户请求需要生成或润色艺术类，且有明确的主题要求时，应调用此工具，请注意：专业作图相关的请求（如流程图，序列图，统计图，甘特图，旅程图等）并不适用该函数，请使用其他函数解决。\"}\n{\"name\": \"generate_ppt\", \"description\": \"用于生成有明确主题ppt。若用户请求需要生成或润色ppt，且有明确的主题要求时，应调用此工具。\"}\n{\"name\": \"generate_mindmap\", \"description\": \"用于生成有明确主题思维导图。若用户请求需要生成或润色思维导图，且有明确的主题要求时，应调用此工具。\"}\n{\"name\": \"search_image\", \"description\": \"用于网络搜图。若用户请求需要搜索网络图片时，应调用此工具。\", \"parameters\": {\"type\": \"object\", \"properties\": {\"query\": {\"type\": \"string\", \"description\": \"搜索关键字。可包含多组关键词，关键词之间用空格区分，提取搜索主体。\"}}, \"required\": [\"query\"]}}\n</tools> \n\n# 环境信息\n- 今天的日期：2025年03月21日"
                    # if m["role"] == "assistant" and m["type"] == "code":
                    #     code = json.loads(m["content"])
                    #     if code["function"] == "image":
                    #         code["function"] = "generate_image"
                    #     if code["function"] == "mindmap":
                    #         code["function"] = "generate_mindmap"
                    #     m["content"] = json.dumps(code,ensure_ascii=False)
                    
                    # if m["role"] == "assistant" and m["type"] == "code":
                    #     code = json.loads(m["content"])
                    #     if code["function"] == "websearch":
                    #         if "prompt" in code:
                    #             del code["prompt"]
                    #             m["content"] = json.dumps(code,ensure_ascii=False)
                        
                    #     # 如果 function 是 chat，检查并删除 longwrite
                    #     elif code["function"] == "chat":
                    #         if "longwrite" in code:
                    #             del code["longwrite"]
                    #             m["content"] = json.dumps(code,ensure_ascii=False)

                                
        #删除code
        # for k,v in prompts.items():
        #     for i,messages in enumerate(v):
        #         j = 0
        #         while j < len(messages):
        #             m = messages[j]
        #             if m["role"] == "assistant" and m["type"] == "code":
        #                 code = json.loads(m["content"])
        #                 if code["function"] == "recommend":
        #                     del messages[j]  # 删除当前满足条件的 m
        #                     # 如果 j 变成最后一个元素，跳出循环
        #                     if j < len(messages):  # 确保下一个元素存在才删除
        #                         del messages[j]  # 删除下一个元素
        #                     else:
        #                         break  # 如果已经是最后一个元素了，直接退出
        #                     # 删除后不增加 j，保持当前位置不变
        #                 else:
        #                     j += 1  # 只有在没有删除元素时才增加 j
        #             else:
        #                 j += 1  # 只有在没有删除元素时才增加 j
        
        #     if len(v) >= 2:
        #         last_index = len(v) - 1
        #         second_last_index = len(v) - 2
        #         # 检查最后两个 messages 的长度
        #         if len(v[last_index]) == len(v[second_last_index]):
        #             del v[last_index]

        prompt = json.dumps(prompts,ensure_ascii=False,indent=2)
        prompt1 = prompt[:30000]
        prompt2 = prompt[30000:60000]
        prompt3 = prompt[60000:90000]
        prompt4 = prompt[90000:120000]
        airsheet.write_xl([prompt1,prompt2,prompt3,prompt4], f'AC{row_index}', sheet_name=self.sheetname)
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")

if __name__ == '__main__':
    # ss = [sheetname,sheetname1,sheetname2,sheetname3,sheetname4,sheetname5,sheetname6,sheetname7,sheetname8]
    # ss = [sheetname]
    ss = [sheetname4]
    for s in ss:
        ai = RunAi(file_id=file_id,sheetname=s,must_have_columns=必须有的列名,skip_col_name=输出列名,clo_num_to_write=输出列编号,max_workers=10)
        ai.run_one = MethodType(run_one, ai)
        ai.run()
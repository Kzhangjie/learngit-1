 # -*- coding: utf-8 -*-
import sys
import os
# 添加父目录到 sys.path 以导入 kllm 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "airsheet_sdk"))

import kllm
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

executor = ThreadPoolExecutor(max_workers=20)
import pandas as pd
import airsheet

file_id = 'cp7L7Vg5iJpO'
offical_wps_sid = 'V02SjPNcvO_92acnd0Xpp1zkURC3QW400a45e9a70052c10daf'
sheetname1 = "websearch"
sheetname2 = "generate_ppt"
sheetname3 = "url_fetch"
sheetname4 = "chat"
sheetname5 = "generate_mindmap"
sheetname6 = "generate_image"
sheetname7 = "data_analysis"
sheetname8 = "processon"
sheetname9 = "table_operation"
sheet_names = [sheetname1, sheetname2, sheetname3, sheetname4, sheetname5, sheetname6, sheetname7, sheetname8, sheetname9]
# sheet_names = [sheetname9]

def ask_translation_Traditional_Chinese(question):
    #选择大模型
    model = kllm.chat.completion('deepseek-chat')
    msgs = [
            {'role': 'system', 'content': """請將我给你原文內容轉換為繁體中文，並保持原有格式（每行一個字符串，用英文引號包裹，行尾逗號，換行符保持不變）。不要改變標點符號、引號和格式，只需要把簡體字轉為繁體字。
            以下是例子：
            原文：
            "Xxx有限公司改成金山办公有限公司",
            "把公司落款名称右对齐",
            "在落款日期前，落款后，添加：'联系人：张经理 联系电话：0477-xxxxxxx'"

            輸出：
            "Xxx有限公司改成金山辦公有限公司",
            "把公司落款名稱右對齊",
            "在落款日期前，落款後，添加：'联系人：張經理 聯繫電話：0477-xxxxxxx'"

            """,},
            {'role': 'user', 'content': f"""原文：{question}
            """,},
        ]


    #打印模型生成的内容(流式输出)
    # for m in model(msgs, stream=True, max_tokens=4000):
    #     print(m, end='')
    full_response = ''
    for m in model(msgs, stream=True, max_tokens=4000):
        chunk = m.content
        full_response += chunk
        print(chunk, end='', flush=True)

    # 循环结束后，full_response 就是完整的 content
    print('\n\n完整回复：', full_response)
    return full_response

def ask_translation_Japanese_language(question):
    #选择大模型
    model = kllm.chat.completion('deepseek-chat')
    msgs = [
            {'role': 'system', 'content': """請將我给你原文內容翻譯成日語，並保持原有格式（每行一個字符串，用英文引號包裹，行尾逗號，換行符保持不變）。不要改變標點符號、引號和格式，只需要翻譯引號內的中文為日語。
            以下是例子：
            原文：
            "Xxx有限公司改成金山办公有限公司",
            "把公司落款名称右对齐",
            "在落款日期前，落款后，添加：'联系人：张经理 联系电话：0477-xxxxxxx'"

            輸出：
            "Xxx有限公司を金山オフィス株式会社に変更する",
            "会社の署名名称を右揃えにする",
            "署名の日付の前後に「連絡先：張マネージャー 電話番号：0477-xxxxxxx」を追加する"

            """,},
            {'role': 'user', 'content': f"""原文：{question}
            """,},
        ]


    #打印模型生成的内容(流式输出)
    # for m in model(msgs, stream=True, max_tokens=4000):
    #     print(m, end='')
    full_response = ''
    for m in model(msgs, stream=True, max_tokens=4000):
        chunk = m.content
        full_response += chunk
        print(chunk, end='', flush=True)

    # 循环结束后，full_response 就是完整的 content
    print('\n\n完整回复：', full_response)
    return full_response

def ask_translation_English_language(question):
    #选择大模型
    model = kllm.chat.completion('deepseek-chat')
    msgs = [
            {'role': 'system', 'content': """Please translate the following content into English, and keep the original format (each line is a string wrapped in double quotes, ending with a comma, line breaks unchanged). Do not change punctuation, quotes, or format — only translate the text inside the quotes.
            
            For example:
            Original:
            "Xxx有限公司改成金山办公有限公司",
            "把公司落款名称右对齐",
            "在落款日期前，落款后，添加：'联系人：张经理 联系电话：0477-xxxxxxx'"

            Output:
            "Change Xxx Co., Ltd. to Kingsoft Office Co., Ltd.",
            "Align the company signature name to the right",
            "Before and after the signature date, add: 'Contact: Manager Zhang  Phone: 0477-xxxxxxx'"

            """,},
            {'role': 'user', 'content': f"""原文：{question}
            """,},
        ]
    full_response = ''
    for m in model(msgs, stream=True, max_tokens=4000):
        chunk = m.content
        full_response += chunk
        print(chunk, end='', flush=True)

    # 循环结束后，full_response 就是完整的 content
    print('\n\n完整回复：', full_response)
    return full_response

def process_one_row(row, i, sheet_name):
    row = row.to_dict()
    question = row['问题1']
    new_text = row['问题']
    # quality_article = row['新内容质量']
    # if pd.notna(quality):
    #     print(f"已有数据: {quality}")
    #     return
    # if pd.notna(quality_article):
    #     print(f"已有数据: {quality_article}")
    #     return
  
    if pd.notna(new_text) :
        print(f"第 {i+2} 行已有内容，跳过")
        # response = ask_translation(question)
        return

    elif pd.notna(question): 
        response = ask_translation_Japanese_language(question)
    # length = len(response)
    airsheet.write_xl(response, f"G{i+2}", sheet_name=sheet_name)
    


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_list = []
        for sheet_name in sheet_names:
            airsheet.init(file_id=file_id, wps_sid=offical_wps_sid, sheet_name=sheet_name)
            print('reading dataset...')
            df = airsheet.xl("A:AR", headers=True, sheet_name=[sheet_name])
            print(df.head())
            for i, row in df.iterrows():
                future = executor.submit(process_one_row, row, i, sheet_name)
                future_list.append(future)
            
            # 如果想要等待所有结果完成，并捕获异常
            for future in concurrent.futures.as_completed(future_list):
                try:
                    # 获取结果（如果 `process_one_row` 有 return，可以在这里拿到）
                    future.result()
                except Exception as e:
                    print(f"线程执行出错: {e}")
          
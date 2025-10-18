import re
import traceback
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from airsheet_sdk import airsheet
import traceback
from api.api_intention_mcp import Copilot
import traceback
import json
from code_session import history_to_chat_messages
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading
import os

load_dotenv()

def run_one(row):
    try:
        answer_type = False
        ans_len = len(row["问题1"].split("ask:")) - 1
        row_index = row["row_index"]
        checks = row["调度断言"].strip().split("\n")
        active_sheet = row["active_sheet"]
        qs = row["问题1"].split("ask:")
        # print ("==========空格拆分==============")
        # print (qs)
        # print ("==========空格拆分==============")
        qs = [q.strip() for q in qs if q]
        # print ("==========问题拆分==============")
        # print (qs)
        # print ("==========问题拆分==============")

        # 取文件ID，并拼接到问题中
        file_id_1 = re.search(
            r"https://(?:www\.)?kdocs.cn/l/(\w+)", row["文件链接"]
        ).group(1)
        for i in range(len(qs)):
            element = qs[i]
            new_element = f"[上传{row_index}.xlsx](wps365://files/{file_id_1}){element}"  # 生成新格式（文件名自定义）
            # print('---new_element:', new_element)
            qs[i] = new_element  # 替换元素

        num_qs = len(qs)
        print(checks)
        try:
            prompts = json.loads(
                row["prompts"]
                + row.get("prompts1", "")
                + row.get("prompts2", "")
                + row.get("prompts3", "")
            )
            num_prompts_keys = len(prompts.keys())

            schedule_assertion_lines = row["调度断言"].split("\n")
            schedule_assertion_counts = [
                len(line.split()) for line in schedule_assertion_lines
            ]
            all_conditions_met = True
            for i, (k, v) in enumerate(prompts.items()):
                if i < len(schedule_assertion_counts):
                    if len(v) < schedule_assertion_counts[i]:
                        all_conditions_met = False
                        break
                else:
                    all_conditions_met = False
                    break

            if num_prompts_keys != 0 and all_conditions_met == True:
                pass

            else:
                print("处理后的question列表：", qs)
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        function_names = json.loads(
                            answer( qs, row_index, active_sheet, answer_type)
                        )
                        if len(function_names) == num_qs:
                            break
                    except json.JSONDecodeError:
                        pass
                    retry_count += 1
                    print(f"重试第 {retry_count} 次...")

                if retry_count == max_retries:
                    print("达到最大重试次数，无法获取正确长度的 codes")
                else:
                    print("----codes:", function_names)
                    function_ans = judge_function(
                         function_names, checks, row_index, answer_type
                    )

        except json.JSONDecodeError:
            print("prompt解析失败，直接跑工程接口")

    except Exception as e:
        print(traceback.format_exception(e))


def answer( qs, row_index, active_sheet, answer_type):

    messages, function_names, function_code, operation_message, recommend_questions,code_events_list, prompt, session_id = cc.questions(qs, active_sheet)
    print("function_names:", function_names)
    print("function_code:", function_code)
    print("messages:", messages)
    result = messages
    r1 = result[:30000]
    r2 = result[30000:60000]
    r3 = result[60000:90000]
    r4 = result[90000:120000]
    p1 = prompt[:30000]
    p2 = prompt[30000:60000]
    p3 = prompt[60000:90000]
    p4 = prompt[90000:120000]
    print("----开始输入")

    airsheet.write_xl(
        [f"'{session_id}", r1, r2, r3, r4, "", function_code, "", p1, p2, p3, p4],
        f"J{row_index}",
        sheet_name=sheetname,
    )
    airsheet.write_xl(
        str(recommend_questions), f"AI{row_index}", sheet_name=sheetname
    )
    print("----输出完成")
    print("-----输出code")
    airsheet.write_xl([function_code], f"W{row_index}", sheet_name=sheetname)
    airsheet.write_xl(
        [operation_message], f"AY{row_index}", sheet_name=sheetname
    )  # 写入代码
    return function_code



def judge_function( function_names, checks, row_index, answer_type):
    ok = "是"
    details = []

    for index, check in enumerate(checks):
        # 跟踪检查过的 code 项
        checked_codes = []
        function_name = function_names[index]

        if "/" in check:  # 新增规则 1，拆分中间带有/的情况
            parts = check.split("/")
            if not any(part in function_name for part in parts):
                ok = "否"
                details.append(f"第{index + 1}个回答没有满足{check}中的任意一项")
            else:
                matched_parts = [part for part in parts if part in function_name]
                checked_codes.extend(matched_parts)
            continue  # 一旦处理了 / 的情况，跳过本次循环
        else:
            if check not in function_name:
                ok = "否"
                details.append(f"第{index + 1}个回答不符合{check}")
            else:
                continue  # 如果没有 / 的情况，继续处理
        
        extra_codes = []
        for check in checked_codes:
            if  function_name not in check:
                extra_codes.append(function_name)
        if extra_codes:
            ok = "否"
            details.append(f"第{index + 1}个回答多了{', '.join(extra_codes)}")

    if answer_type == True:
        airsheet.write_xl(
            [ok, "\n".join(details)], f"V{row_index}", sheet_name=sheetname
        )
    else:
        airsheet.write_xl(
            [ok, "\n".join(details)], f"X{row_index}", sheet_name=sheetname
        )
    return [ok, "\n".join(details)]


def history_to_prompt( history: dict, qs, row_index):
    messages = history_to_chat_messages(history, qs)
    prompt = json.dumps(messages, ensure_ascii=False, indent=2)
    print("prompt:", prompt)
    prompt1 = prompt[:30000]
    prompt2 = prompt[30000:60000]
    prompt3 = prompt[60000:90000]
    prompt4 = prompt[90000:120000]
    airsheet.write_xl(
        [prompt1, prompt2, prompt3, prompt4], f"R{row_index}", sheet_name=sheetname
    )
    return prompt


if __name__ == "__main__":
    file_id = "cp7L7Vg5iJpO"
    sheetname1 = "websearch"
    sheetname2 = "generate_ppt"
    sheetname3 = "url_fetch"
    sheetname4 = "chat"
    sheetname5 = "generate_mindmap"
    sheetname6 = "generate_image"
    sheetname7 = "data_analysis"
    sheetname9 = "table_operation"
    必须有的列名 = ["prompts"]
    输出列名 = "模型返回"
    输出列编号 = "Y"
    # 内网url
    cc = Copilot(is_test=True, model_url="", custom_headers={}, search_engines="")

    ss = [sheetname1, sheetname2, sheetname3, sheetname4, sheetname5, sheetname6, sheetname7, sheetname9]
    # ss = [sheetname7]
    wps_sid = os.environ.get("WPS_SID")
    for sheetname in ss:
        print(f"开始处理工作表: {sheetname}")
        airsheet.init(file_id=file_id, wps_sid=wps_sid, sheet_name=sheetname)
        df = airsheet.xl("A:FZ", headers=True, sheet_name=[sheetname])
        columns_to_drop = [col for col in df.columns if col == "" or col is None]
        df = df.drop(columns=columns_to_drop)
        df["row_index"] = df.index + 2
        df.fillna("", inplace=True)
        datas = df.to_dict(orient="records")
        datas = [data for data in datas if data.get("模型调度断言总体") == ""]
        # 使用线程池并行处理数据
        max_workers = 8  # 最大线程数，避免创建过多线程
        print(f"使用 {max_workers} 个线程并行处理 {len(datas)} 条数据")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = [executor.submit(run_one, data) for data in datas]
            
            # 等待所有任务完成
            for i, future in enumerate(futures):
                try:
                    future.result()  # 获取结果，会抛出异常如果有的话
                    print(f"任务 {i+1}/{len(datas)} 完成")
                except Exception as e:
                    print(f"任务 {i+1} 执行失败: {e}")
        
        print("所有任务处理完成")

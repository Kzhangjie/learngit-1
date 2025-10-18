import re
import traceback
from airsheet_sdk import airsheet
import traceback
import json
from kuangzhirong.api.api_intention_mcp import Copilot
from code_session import chat_stream
import traceback
import json
from gen_prompt import extra_codes
from code_session import history_to_chat_messages, trans_chat_messages_2_messages
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv
load_dotenv()

file_id = "cs9yL3svoA02"
sheetname1 = "websearch"
sheetname2 = "generate_ppt"
sheetname3 = "url_fetch"
sheetname4 = "chat"
sheetname5 = "generate_mindmap"
sheetname6 = "generate_image"
sheetname7 = "data_analysis"
sheetname8 = "processon"
sheetname9 = "table_operation"
必须有的列名 = ["prompts"]
输出列名 = "模型返回"
输出列编号 = "Y"
# 内网url
cc = Copilot(is_test=True, model_url="", custom_headers={}, search_engines="")

# 添加线程锁，确保airsheet写入操作的线程安全
airsheet_lock = threading.Lock()

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
        print(f"线程处理行 {row_index}: {checks}")
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
                print(f"线程 {row_index} 处理后的question列表：", qs)
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
                    print(f"线程 {row_index} 重试第 {retry_count} 次...")

                if retry_count == max_retries:
                    print(f"线程 {row_index} 达到最大重试次数，无法获取正确长度的 codes")
                else:
                    print(f"线程 {row_index} ----codes:", function_names)
                    function_ans = judge_function(
                         function_names, checks, row_index, answer_type
                    )

        except json.JSONDecodeError:
            print(f"线程 {row_index} prompt解析失败，直接跑工程接口")

    except Exception as e:
        print(f"线程 {row_index} 出现异常:", traceback.format_exception(e))


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

    # 使用线程锁保护airsheet写入操作
    with airsheet_lock:
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
    print(f"线程 {row_index} prompt:", prompt)
    prompt1 = prompt[:30000]
    prompt2 = prompt[30000:60000]
    prompt3 = prompt[60000:90000]
    prompt4 = prompt[90000:120000]
    
    # 使用线程锁保护airsheet写入操作
    with airsheet_lock:
        airsheet.write_xl(
            [prompt1, prompt2, prompt3, prompt4], f"R{row_index}", sheet_name=sheetname
        )
    return prompt


if __name__ == "__main__":
    import os
    
    # 定义所有需要处理的sheetname
    all_sheetnames = [sheetname1, sheetname2, sheetname3, sheetname4, sheetname5, sheetname6, sheetname7, sheetname8, sheetname9]
    
    wps_sid = os.environ.get("WPS_SID")
    
    # 遍历所有sheetname
    for sheetname in all_sheetnames:
        print(f"开始处理工作表: {sheetname}")
        
        try:
            airsheet.init(file_id=file_id, wps_sid=wps_sid, sheet_name=sheetname)
            df = airsheet.xl("A:FZ", headers=True, sheet_name=[sheetname])
            columns_to_drop = [col for col in df.columns if col == "" or col is None]
            df = df.drop(columns=columns_to_drop)
            df["row_index"] = df.index + 2
            df.fillna("", inplace=True)
            datas = df.to_dict(orient="records")
            datas = [data for data in datas if data.get("模型调度断言总体") == ""]
            
            if not datas:
                print(f"工作表 {sheetname} 没有需要处理的数据，跳过...")
                continue
            
            # 使用多线程处理数据
            max_workers = 4  # 可以根据需要调整线程数量
            print(f"开始使用 {max_workers} 个线程处理工作表 {sheetname} 的 {len(datas)} 条数据...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_data = {executor.submit(run_one, data): data for data in datas}
                
                # 处理完成的任务
                completed_count = 0
                for future in as_completed(future_to_data):
                    data = future_to_data[future]
                    try:
                        result = future.result()
                        completed_count += 1
                        print(f"工作表 {sheetname}: 已完成 {completed_count}/{len(datas)} 个任务，行索引: {data.get('row_index', 'unknown')}")
                    except Exception as exc:
                        print(f"工作表 {sheetname} 任务执行异常，行索引 {data.get('row_index', 'unknown')}: {exc}")
            
            print(f"工作表 {sheetname} 的所有任务已完成！")
            
        except Exception as e:
            print(f"处理工作表 {sheetname} 时发生错误: {e}")
            continue
    
    print("所有工作表处理完成！")

import copy
from datetime import datetime, timedelta
import os
import requests
import logging
from kae_util import Kae, kae_cookie, default_config, configs, get_time_data


import re
import json
import time
import traceback

from logger_utils import getLogger

logger = getLogger("kae_logs_go")
# logger = logging


def parse_chunked_body(chunked_body):
    return chunked_body.split("\\r\\n")[1]


def parse_http_log_catch(log_text):
    try:
        return parse_http_log(log_text)
    except Exception as e:
        logger.error(f"parse_http_log error {traceback.format_exception(e)}")
        logger.error(log_text)
        return None


def parse_http_log(log_text):
    # 按双换行符分割请求和响应部分
    # tk_pattern = "deepseek-reasoner模型计算tokens"
    # mk_pattern = "deepseek-reasoner tokenizer计算tokens"

    # 使用正则表达式来匹配"Doubao-1.5-pro-XXXk模型计算tokens"模式
    tk_pattern = r"Doubao-1\.5-pro-\d+k模型计算tokens"
    mk_pattern = r"Doubao-1\.5-pro-\d+k tokenizer计算tokens"

    """
    time="2025-04-21T20:04:40+08:00" level=info msg="deepseek-reasoner模型计算tokens：prompt tokens=7, completion tokens=875, total tokens=882" func="solution/aigc/cc/logic.(*Session).SendReasoningStream.func1" file="@aigc/cc/logic/session.go:333" model=deepseek-reasoner operation=/copilotpb.Copilot/CreateCompletion session_id=8898334665343109 traceid=dd0f086cfb89f3529dbb54a8819aeaa0
    time="2025-04-21T20:04:40+08:00" level=info msg="deepseek-reasoner tokenizer计算tokens：prompt tokens=4, completion tokens=888, total tokens=892" func="solution/aigc/cc/logic.(*Session).SendReasoningStream.func1" file="@aigc/cc/logic/session.go:347" model=deepseek-reasoner operation=/copilotpb.Copilot/CreateCompletion session_id=8898334665343109 traceid=dd0f086cfb89f3529dbb54a8819aeaa0
    
    """
    if re.search(tk_pattern, log_text):
        logger.info(log_text)
        # 解析模型计算日志
        log_type = "模型"
        # 提取session_id
        session_match = re.search(r"session_id=(\d+)", log_text)
        session_id = session_match.group(1) if session_match else None

        # 提取prompt tokens
        tokens_match = re.search(r"prompt tokens=(\d+)", log_text)
        prompt_tokens = int(tokens_match.group(1)) if tokens_match else None

        return (log_type, session_id, prompt_tokens)
    elif re.search(mk_pattern, log_text):
        logger.info(log_text)
        # 解析tokenizer计算日志
        log_type = "计算"
        # 提取session_id
        session_match = re.search(r"session_id=(\d+)", log_text)
        session_id = session_match.group(1) if session_match else None

        # 提取prompt tokens
        tokens_match = re.search(r"prompt tokens=(\d+)", log_text)
        prompt_tokens = int(tokens_match.group(1)) if tokens_match else None

        return (log_type, session_id, prompt_tokens)
    else:
        return None


# Add main method for testing
if __name__ == "__main__":
    # Create a Kae instance for the "gray" environment
    skip_no_ratio = False  # 修改为False，因为我们会先清理没有比例的记录
    kae = Kae("dcl", logger=logger, parse_http_log_catch=parse_http_log_catch)
    # results = []
    # for i in range(100):
    #     try:
    #         rs = kae.get_session_reqs_raw(
    #             " tokens ",
    #             delta_time=100000,
    #             wait=0,
    #             query="",
    #             size=1000,
    #             offset=i * 1000,
    #         )
    #         results.extend(rs)
    #     except Exception as e:
    #         logger.error(f"Error fetching session requests: {e}")

    # 读取session_ids.txt，构建session_id到文件路径的映射
    session_to_filepath = {}
    error_sessions = set()  # 存储包含error的session_id
    session_ids_file = r"D:\projects\llm_batch_test\session_ids_doubao.txt"

    if os.path.exists(session_ids_file):
        with open(session_ids_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 3:  # 确保行有足够的部分
                    file_path = parts[0]
                    session_id = parts[-1]  # session_id在最后一个位置
                    session_to_filepath[session_id] = file_path

                    # 检查第2列和第3列是否包含"error"
                    if len(parts) >= 3 and (
                        "error" in parts[1].lower() or "error" in parts[2].lower()
                    ):
                        error_sessions.add(session_id)
                        print(f"发现error session: {session_id}")
        print(
            f"从{session_ids_file}中读取了{len(session_to_filepath)}个session_id到文件路径的映射，其中{len(error_sessions)}个包含error"
        )
    print(session_to_filepath)

    # 准备CSV文件并读取已处理的session_id
    csv_file = "d:\\projects\\llm_batch_test\\token_comparison_doubao.csv"
    processed_sessions = set()

    # 先清理CSV文件中没有比例的记录
    if os.path.exists(csv_file):
        print("开始清理CSV文件中没有比例的记录...")
        with open(csv_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        header = (
            lines[0]
            if lines
            else "文件路径,session_id,模型prompt_tokens,计算prompt_tokens,计算/模型比例,差距\n"
        )
        valid_lines = [header]
        skipped_lines = 0

        # 检查每一行，保留有比例的行或包含error的session_id的行
        for line in lines[1:]:
            parts = line.strip().split(",")
            if len(parts) >= 5:
                session_id = parts[1] if len(parts) > 1 else ""
                # 如果有比例或session_id在error_sessions中，则保留
                if parts[4].strip() or session_id in error_sessions:
                    valid_lines.append(line)
                    processed_sessions.add(session_id)  # 添加到已处理集合
                else:
                    skipped_lines += 1
            else:
                skipped_lines += 1

        # 保存清理后的文件
        with open(csv_file, "w", encoding="utf-8") as f:
            f.writelines(valid_lines)

        print(
            f"清理完成，删除了 {skipped_lines} 条没有比例且不包含error的记录，保留了 {len(valid_lines) - 1} 条记录"
        )
    else:
        # 如果CSV文件不存在，创建文件并写入表头
        with open(csv_file, "w", encoding="utf-8") as f:
            f.write(
                "文件路径,session_id,模型prompt_tokens,计算prompt_tokens,计算/模型比例,差距\n"
            )
            print("创建了新的CSV文件并写入表头")

    # 记录处理的记录数
    processed_count = 0
    skipped_count = 0

    # 逐个处理每个session_id
    for session_id, file_path in session_to_filepath.items():
        # 检查是否已处理过该session_id
        if session_id in processed_sessions:
            skipped_count += 1
            if skipped_count % 10 == 0:
                print(f"已跳过 {skipped_count} 条已处理记录")
            continue

        try:
            rs = kae.get_session_reqs_raw(
                f" tokens AND {session_id}",
                delta_time=600,
                wait=0,
                query="",
                size=100,
            )

            # 处理当前session_id的结果
            session_data = {"模型": None, "计算": None}
            for result in rs:
                if result is None:
                    continue

                log_type, res_session_id, prompt_tokens = result
                if res_session_id == session_id:
                    session_data[log_type] = prompt_tokens

            # 准备CSV行数据
            model_tokens = session_data["模型"]
            calc_tokens = session_data["计算"]

            # 计算比例，处理可能的None值
            ratio = ""
            gap = ""
            if model_tokens and calc_tokens:
                ratio = calc_tokens / model_tokens
                # 判断差距大小：如果比例在0.7~1.3之间为"小"，否则为"大"
                if ratio < 0.7:
                    gap = "小2"
                elif 0.77 <= ratio < 0.9:
                    gap = "小1"
                elif 0.9 <= ratio < 1.0:
                    gap = "小0"
                elif 1.0 <= ratio < 1.1:
                    gap = "大0"
                elif 1.1 <= ratio < 1.3:
                    gap = "大1"
                elif ratio >= 1.3:
                    gap = "大2"
                    # 如果设置跳过没有比例的记录且没有比例，则跳过写入文件
            if skip_no_ratio and (model_tokens is None or calc_tokens is None):
                logger.info(f"跳过没有比例的记录: session_id={session_id}")
                continue

            # 构建CSV行并追加到文件
            row = f"{file_path},{session_id},{model_tokens if model_tokens else ''},{calc_tokens if calc_tokens else ''},{ratio},{gap}"
            with open(csv_file, "a", encoding="utf-8") as f:
                f.write(row + "\n")

            processed_count += 1
            if processed_count % 10 == 0:
                print(
                    f"已处理 {processed_count}/{len(session_to_filepath) - skipped_count} 条新记录"
                )

        except Exception as e:
            logger.error(f"处理session_id {session_id}时出错: {e}")
            # 记录错误但继续处理下一个

    print(f"数据已写入: {csv_file}")
    print(f"共处理 {processed_count} 条新记录，跳过 {skipped_count} 条已处理记录")

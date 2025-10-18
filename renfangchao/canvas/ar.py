import concurrent.futures
import glob
import json
import os
import threading
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from renfangchao.canvas.gen_1_answer import parse_code
from run_batch.run_ai import RunAi

# 创建一个线程锁用于文件写入
file_lock = threading.Lock()
# 主程序
api = Copilot(
    is_test=True,
    model_url="",
    wps_sid="",
    custom_headers={"X-Cc-Region": "dcl"},
    search_engines="",
    agent="",
)


def process_md_file(fi, api, output_file):
    """处理单个MD文件，调用API并存储session_id"""
    try:
        with open(fi, "r", encoding="utf-8") as f:
            text = f.read()

        historys, rs, session_id = api.questions(
            [
                {
                    "question": f"不要多想，只输出以下文档第一个字：\n{text}",
                    "reasoning": False,
                }
            ],
            "",
            with_history=False,
        )  # type: ignore
        session_id = str(session_id)
        is_error = "error" if "error" in rs[0][0] else "success"
        is_token_error = (
            "PromptTokenExceedLimit"
            if "PromptTokenExceedLimit" in rs[0][0]
            else "success"
        )
        # 打印当前处理的文件和session_id
        print(f"处理文件: {fi}")
        print(f"Session ID: {session_id}")

        # 安全地将session_id写入文件
        with file_lock:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"{fi},{is_error},{is_token_error},{session_id}\n")
        return True

    except Exception as e:
        print(f"处理文件 {fi} 时出错: {str(e)}")
        traceback.print_exc()
        return False


# 定义目标目录和输出文件
target_dir = r"D:\projects\md_all_uni"
output_file = r"D:\projects\llm_batch_test\session_ids_doubao.txt"

# 读取已处理的文件列表
processed_files = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and "," in line:
                file_path = line.split(",")[0].strip()
                processed_files.add(file_path)
    print(f"已从输出文件中发现 {len(processed_files)} 个处理过的文件")

# 查找所有md文件
all_md_files = glob.glob(os.path.join(target_dir, "**/*.md"), recursive=True)

# 过滤掉已处理的文件
md_files = [file for file in all_md_files if file not in processed_files]
print(f"总共找到 {len(all_md_files)} 个MD文件，其中 {len(md_files)} 个需要处理")

# 使用线程池执行10并发
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    # 创建一个任务列表
    futures = [
        executor.submit(process_md_file, fi, api, output_file) for fi in md_files
    ]

    # 等待所有任务完成
    for future in concurrent.futures.as_completed(futures):
        future.result()

print(f"处理完成，所有session_id已保存到: {output_file}")

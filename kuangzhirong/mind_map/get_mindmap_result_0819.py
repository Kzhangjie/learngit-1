import re
import traceback
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from airsheet_sdk import airsheet
import traceback
import json
from api.api_generate_mindmap import Copilot
import traceback
import json
from mind_map.code_session import history_to_chat_messages
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv
import os
from api.api_gateway import AIGateway, ChatMessage
load_dotenv()

# 添加线程锁，确保airsheet写入操作的线程安全
airsheet_lock = threading.Lock()

def run_one(row):
    try:
        answer_type = False
        row_index = row["row_index"]
        qs = row["问题"].split("ask:")
        qs = [q.strip() for q in qs if q]

        try:
            # 取文件ID，并拼接到问题中
            file_id_1 = re.search(
                r"https://(?:www\.)?kdocs.cn/l/(\w+)", row["文件链接"]
            ).group(1)
            for i in range(len(qs)):
                element = qs[i]
                new_element = f"[上传{row_index}.xlsx](wps365://files/{file_id_1}){element}"  # 生成新格式（文件名自定义）
                # print('---new_element:', new_element)
                qs[i] = new_element  # 替换元素
        except Exception as e:
            print(f"线程 {row_index} 取文件ID失败: {e}")
            
        num_qs = len(qs)
        try:

            print(f"线程 {row_index} 处理后的question列表：", qs)
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    function_names = json.loads(
                        answer(qs, row_index)
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

        except json.JSONDecodeError:
            print(f"线程 {row_index} prompt解析失败，直接跑工程接口")

    except Exception as e:
        print(f"线程 {row_index} 出现异常:", traceback.format_exception(e))

def get_mind_map_content(prompt):
    result = ""
    prompt_json = json.loads(prompt)[-1]
    for message in prompt_json:
        if message["type"] == "mind_map":
            result = message["content"]
    if result == "":
        # 解析出最后一个type为text的content
        for message in prompt_json:
            if message["type"] == "text":
                result = message["content"]
    return result

def answer( qs, row_index):

    messages, function_names, function_code, operation_message, recommend_questions,code_events_list, prompt, session_id = cc.questions(qs)
    print("session_id:", session_id)
    print("prompt:", prompt)
    print("----开始输入")
    mind_map_content = get_mind_map_content(prompt)
    print("mind_map_content:", mind_map_content)
    airsheet.write_xl(
        [f"'{session_id}", mind_map_content],
        f"E{row_index}",
        sheet_name=sheetname,
    )
    print("----输出完成")
    print("-----输出code")
    return function_code


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


def judge_mindmap_result(question, mindmap_content, row_index):
    ai = AIGateway(model="Doubao-Seed-1.6", provider="doubao", temperature=0.1, token=AI_GATEWAY_TOKEN_V2)
    prompt = """
# Role:
你是一位专业的思维导图分析师和AI模型评测专家。

# Task:
你的任务是根据我提供的“主题”和AI生成的“思维导图内容”，按照以下定义的“评测框架”进行严格、客观的评分，并以指定的JSON格式输出结果。
# Scoring Scale:
请为每个评测维度打分，分值为1-5分。
- **5分 (优秀):** 全面超出预期，结构清晰，内容富有洞察力，几乎无需修改。
- **4分 (良好):** 满足绝大部分要求，结构合理，内容翔实，有少量可改进之处。
- **3分 (合格):** 基本完成任务，但存在结构不清晰、内容宽泛或信息缺失等问题。
- **2分 (较差):** 未能很好地完成任务，结构混乱或内容有严重缺陷。
- **1分 (劣质):** 完全失败，内容空洞、逻辑不通或严重偏离主题。

# Evaluation Framework & Weights:

### 1. 结构逻辑性 (Structural Logic) - 权重 25%
- **层次清晰度:** 父子节点关系是否明确？整体是否呈现出良好的树状结构？
- **逻辑关联性:** 同级节点之间、父子节点之间的逻辑关系是否合理（如并列、递进、总分）？是否存在内容错配（如将“宣传”放在“活动内容”下）？

### 2. 内容准确性 (Content Accuracy & Relevance) - 权重 20%
- **紧扣主题:** 所有分支和节点是否都紧密围绕核心主题展开？
- **事实准确性:** 如果内容涉及客观事实、数据或定义，是否准确无误？（若不涉及，此项可侧重于上下文的合理性）

### 3. 信息价值 (Information Value) - 权重 25%
- **覆盖全面性:** 是否覆盖了该主题下的关键方面？是否存在明显的信息遗漏？
- **信息密度:** 内容是具体、有价值的信息，还是空洞、重复的“废话”？
- **深度与广度:** 在符合主题定位的前提下，内容是否有足够的广度，并在关键节点上有适当的深度？

### 4. 指令遵循度 (Instruction Adherence) - 权重 15%
- **核心指令遵循:** 是否围绕用户指定的核心主题和主要分支进行构建？
- **格式与风格遵循:** 是否遵循了用户要求的输出格式（如Markdown）、风格（如“简洁”、“有创意”）等额外指令？

### 5. 启发与拓展性 (Inspirational & Extensible Value) - 权重 15%
- **启发性:** 内容是否能引发用户的进一步思考，提供新的视角或创意？
- **可拓展性:** 结构是否清晰、开放，便于用户在此基础上进行修改、补充和深化？
    """
    prompt_1 = prompt + f'''
    # Content to be Evaluated:

    - **主题:**
    """
    {str(question)}
    """

    - **思维导图内容 (通常为Markdown格式):**
    """
    {mindmap_content}
    """

    # Output Requirements:
    请严格按照以下JSON格式输出你的评测结果。不要在JSON代码块之外添加任何额外的介绍、总结或解释性文字。

    '''

    prompt_all = prompt_1 + """{
    "overall_score": <根据上述权重计算出的加权总分，保留一位小数>,
    "detailed_scores": [
        {
        "dimension": "结构逻辑性",
        "score": <1-5之间的整数或浮点数>,
        "justification": "<对该项得分的详细、客观的理由，明确指出优点和缺点>"
        },
        {
        "dimension": "内容准确性",
        "score": <1-5之间的整数或浮点数>,
        "justification": "<对该项得分的详细、客观的理由，明确指出优点和缺点>"
        },
        {
        "dimension": "信息价值",
        "score": <1-5之间的整数或浮点数>,
        "justification": "<对该项得分的详细、客观的理由，明确指出优点和缺点>"
        },
        {
        "dimension": "指令遵循度",
        "score": <1-5之间的整数或浮点数>,
        "justification": "<对该项得分的详细、客观的理由，明确指出优点和缺点>"
        },
        {
        "dimension": "启发与拓展性",
        "score": <1-5之间的整数或浮点数>,
        "justification": "<对该项得分的详细、客观的理由，明确指出优点和缺点>"
        }
    ],
    "overall_comment": {
        "strengths": "<用一两句话总结该思维导图最主要的优点>",
        "weaknesses": "<用一两句话总结该思维导图最主要的待改进之处>"
    }
    }"""
    messages = [
        ChatMessage(role="user", content=prompt_all)
    ]
    response = ai.request(messages, stream=False)
    score_result = response.json().get("choices")[0].get("text")
    score_result_json = json.loads(score_result)
    detailed_scores = score_result_json.get("detailed_scores")
    with airsheet_lock:
        for detailed_score in detailed_scores:
            dimension = detailed_score.get("dimension")
            score = detailed_score.get("score")
            justification = detailed_score.get("justification")
            overall_comment = score_result_json.get("overall_comment")
            strengths = overall_comment.get("strengths")
            weaknesses = overall_comment.get("weaknesses")
            if dimension == "结构逻辑性":
                airsheet.write_xl(
                    [score, justification], f"H{row_index}", sheet_name=sheetname
                )
            elif dimension == "内容准确性":
                airsheet.write_xl(
                    [score, justification], f"J{row_index}", sheet_name=sheetname
                )
            elif dimension == "信息价值":
                airsheet.write_xl(
                    [score, justification], f"L{row_index}", sheet_name=sheetname
                )
            elif dimension == "指令遵循度":
                airsheet.write_xl(
                    [score, justification], f"N{row_index}", sheet_name=sheetname
                )
            elif dimension == "启发与拓展性":
                airsheet.write_xl(
                    [score, justification], f"P{row_index}", sheet_name=sheetname
                )
            airsheet.write_xl(
                [strengths, weaknesses], f"R{row_index}", sheet_name=sheetname
            )
        overall_score = score_result_json.get("overall_score")
        airsheet.write_xl(
            [overall_score], f"G{row_index}", sheet_name=sheetname
        )


def get_mindmap_result(datas):
    # 使用多线程处理数据
    max_workers = 8  # 可以根据需要调整线程数量
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


def judge_mindmap_result_single(data):
    """单个数据的评测函数，用于多线程调用"""
    row_index = data["row_index"]
    question = data["问题"].split("ask:")
    question = [q.strip() for q in question if q]
    mindmap_content = data["模型结果"]
    result = judge_mindmap_result(question, mindmap_content, row_index)
    print(f"行 {row_index} 评测完成")
    return result

def judge_mindmap_result_all(datas):
    """多线程方式评测所有思维导图结果"""
    max_workers = 8  # 可以根据需要调整线程数量
    print(f"开始使用 {max_workers} 个线程评测 {len(datas)} 条思维导图结果...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_data = {executor.submit(judge_mindmap_result_single, data): data for data in datas}
        
        # 处理完成的任务
        completed_count = 0
        for future in as_completed(future_to_data):
            data = future_to_data[future]
            try:
                result = future.result()
                completed_count += 1
                print(f"评测进度: 已完成 {completed_count}/{len(datas)} 个任务，行索引: {data.get('row_index', 'unknown')}")
            except Exception as exc:
                print(f"评测任务执行异常，行索引 {data.get('row_index', 'unknown')}: {exc}")
    
    print(f"所有思维导图评测任务已完成！")


def main(file_id,sheetname):
    
    # 定义所有需要处理的sheetname
    all_sheetnames = [sheetname]
    
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
            #获取脑图结果
            datas = [data for data in datas if data.get("模型结果") == ""]
            get_mindmap_result(datas) 
             
             #跑评测结果的时候需要注释掉
            # datas = [data for data in datas if data.get("评分结果") == ""]
            # judge_mindmap_result_all(datas)
            
            if not datas:
                print(f"工作表 {sheetname} 没有需要处理的数据，跳过...")
                continue
            
            
        except Exception as e:
            print(f"处理工作表 {sheetname} 时发生错误: {e}")
            continue
    
    print("所有工作表处理完成！")

if __name__ == "__main__":
    # 简中：cjiviiceXwRr
    # 中繁：cj6bUeSv1gwG
    # 日文：csup4pNaFT8C
    # 英语：cvCQ9NovpNpi
    #file_ids = ["csup4pNaFT8C","cvCQ9NovpNpi","cjiviiceXwRr","cj6bUeSv1gwG"]
    file_ids = ["cjiviiceXwRr"]
    sheetname = "演示copilot"        #表格copilot、演示copilot、PDF copilot、文字canvas、AP canvas
    AI_GATEWAY_TOKEN_V2 = os.environ.get("AI_GATEWAY_TOKEN_V2")
    # 内网url
    cc = Copilot(is_test=True, model_url="", custom_headers={}, search_engines="")
    for file_id in file_ids:
        main(file_id, sheetname)
    

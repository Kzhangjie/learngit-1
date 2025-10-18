from types import MethodType
from run_batch.run_code import RunCode
from run_batch.run_ai import RunAi
import airsheet
import traceback
import json
import re

file_id = "ctI6Ti36VX9x"  # 文件
sheetname = "wry-temp"
列名 = "planner"
必须有的列名 = [f"{列名}1"]
输出列名 = "planner_clean1"  # 表示会跳过"答案"列已经有内容的行。
输出列编号 = ["BE", "BJ"]  # 表示从把答案写到B列
msg列名 = "messages"
minimax列名 = "minimax"
from renfangchao.cc_server.as_utils import split_string, get_long_text

from deepdiff import DeepDiff
from renfangchao.cc_server.cutting import cutting

import re


def format_links_string(input_string):
    # Define regex pattern to match the links and their corresponding titles
    pattern = r"\[(.*?)\]\((.*?)\)"

    # Replace all matches using regex with fixed template format
    formatted_string = re.sub(pattern, "[链接标题](链接URL)", input_string)

    return formatted_string


def format_links_full_string(input_string):
    # Define regex pattern to match the links and their corresponding titles, along with additional info like publication date and summary
    pattern = r"\[(.*?)\]\((.*?)\)\n- 发布时间: (.*?)\n- 摘要: (.*?)"

    # Replace all matches using regex with the new fixed template format, using a fixed date and fixed summary text
    formatted_string = re.sub(
        pattern,
        "[链接标题](链接URL)\n- 发布时间: 2012年12月12日 12:12:12(CST) 星期三\n- 摘要: 摘要内容",
        input_string,
    )

    return formatted_string


def replace_dynamic(text):
    patterns = {
        r"今天是:\d{4}-\d{2}-\d{2}。": "今天是:2012-12-12。",
        r"\d{4}年\d{2}月\d{2}日 星期[一二三四五六日]": "2012年12月12日 星期三",
        r"<question>[^<]*</question>": "<question>问题</question>",
        r"<answer>[^<]*</answer>": "<answer>答案</answer>",
        r"<大纲>[^<]*</大纲>": "<大纲>具体内容</大纲>",
        r"<这是已经完成的内容>[^<]*</这是已经完成的内容>": "<这是已经完成的内容>具体内容</这是已经完成的内容>",
        r"<当前指定的章节>[^<]*</当前指定的章节>": "<当前指定的章节>具体内容</当前指定的章节>",
    }
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(
        r"(<document_type>)(jpeg|png|jpg)(</document_type>)(.*?)(<document_content>)(.*?)(</document_content>)",
        r"\1\2\3\5文档内容\7",
        text,
        flags=re.DOTALL,
    )
    return text


def string_json(text) -> str:
    return json.dumps(text, ensure_ascii=False)[1:-1]


def get_request_body_text(text):
    reqs = []
    rs = json.loads(text)
    for r in rs:
        reqs.append(r["request"]["body"])
    text = json.dumps(reqs, ensure_ascii=False, indent=2)
    return split_string(text)


def get_req_msgs(text):
    reqs = []
    for r in json.loads(text):
        body = r["request"]["body"]
        msg = json.loads(body)["messages"]
        reqs.append(msg)
    return reqs


def replace_in_json(text, old, new):
    old_in_json = string_json(old)
    text = text.replace(old_in_json, new)
    return text


def run_one(self, row):
    try:
        planner_text = get_long_text(row, 列名)
        planner_text = replace_dynamic(planner_text)
        minimax_text = get_long_text(row, minimax列名)
        minimax_text = replace_dynamic(minimax_text)

        msg_text = get_long_text(row, msg列名)
        msgs = json.loads(msg_text)
        executions = []
        codes = []
        websearch_results = []
        search_querys = []
        search_promots = []
        for m in msgs:
            if m.get("role") == "assistant" and m.get("type") in [
                "text",
                "ppt_outline_text",
            ]:
                text = m["content"]
                # print(text[:10], "裁剪前", len(text))
                executions.append(text)
                text = cutting(m["content"])
                # print(text[:10], "裁剪后", len(text))
                executions.append(text)
            if m.get("role") == "assistant" and m.get("type") == "code":
                code = json.loads(m["content"])
                if code.get("function", "") == "websearch":
                    search_querys.append(code["query"])
                    search_promots.append(code["prompt"])
                c = json.dumps(code, ensure_ascii=False)
                codes.append(c)
            if m.get("role") == "assistant" and m.get("type") == "websearch_result":
                results = json.loads(m["content"])
                websearch_results.extend(results)
        for i, code in enumerate(codes):
            planner_text = replace_in_json(planner_text, code, f"<^code{i}^>")
        for i, execution in enumerate(executions):
            minimax_text = replace_in_json(minimax_text, execution, f"<^exec{i}^>")
            planner_text = replace_in_json(planner_text, execution, f"<^exec{i}^>")
        for i, websearch_result in enumerate(websearch_results):
            search_minmax_format = f'[{websearch_result.get("title","")}]({websearch_result.get("url","")})\n- 发布时间: {websearch_result.get("time_desc","")}\n- 摘要: {websearch_result.get("summary","")}'
            search_code_format = f'[{websearch_result.get("title","")}]({websearch_result.get("url","")})'
            search_minimax_xml = f'<document_name>{websearch_result.get("title","")}</document_name>\n<document_content>{websearch_result.get("summary","")}'

            planner_text = replace_in_json(
                planner_text, search_code_format, f"<^search_code_format^>"
            )
            minimax_text = replace_in_json(
                minimax_text, search_minmax_format, f"<^search_minmax_format^>"
            )
            minimax_text = replace_in_json(
                minimax_text, search_minimax_xml, f"<^search_minimax_xml^>"
            )
        for i, search_query in enumerate(search_querys):
            minimax_text = replace_in_json(
                minimax_text, search_promots[i], f"<^search_promots{i}^>"
            )
            query_xml = f"<user_question>{search_query}</user_question>"
            minimax_text = replace_in_json(minimax_text, query_xml, f"<^query_xml{i}^>")

        r_planner = get_request_body_text(planner_text)
        r_minimax = get_request_body_text(minimax_text)
        airsheet.write_xl(
            r_planner, f"{输出列编号[0]}{row['row_index']}", sheet_name=sheetname
        )
        airsheet.write_xl(
            r_minimax, f"{输出列编号[1]}{row['row_index']}", sheet_name=sheetname
        )
    except Exception as e:
        print(traceback.format_exception(e))


if __name__ == "__main__":
    code = RunAi(
        file_id=file_id,
        sheetname=sheetname,
        must_have_columns=必须有的列名,
        skip_col_name=输出列名,
        clo_num_to_write=输出列编号,
    )
    code.run_one = MethodType(run_one, code)
    code.run()

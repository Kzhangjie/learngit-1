import json
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from run_batch.run_ai import RunAi

file_id = "cn9eakbcOkFk"  # 文件
default_question_config = {
    # "command_args": {"disable_websearch": False},
    "reasoning": False,
    "context": {
        "enable_canvas_mode": True,
        "agent": "WPP",
        "file_code": "001004000",
        # "file_id": {"id": "1155576226052579328", "type": "object"},
    },
}
# sheetname = "ppt"
必须有的列名 = ["session_id"]
输出列名 = ""  # 表示会跳过"答案"列已经有内容的行。
# 输出列名 = ""
输出列编号 = "R"  # 表示从把答案写到B列

ss = [
    "ppt_generate_speaker_notes",
    "ppt_generate_slides_with_pages",
    "generate_ppt",
    "chat",
    "websearch",
    "generate_image",
    "ppt_set_font",
    "generate_mindmap",
]


# ss = [
#     "ppt_generate_slides_with_pages",
# ]
aims = {
    "chat": ["chat"],
    "websearch": ["websearch"],
    "generate_image": ["generate_image"],
    "ppt_set_animation": ["ppt_set_animation"],
    "ppt_set_font": ["ppt_set_font"],
    "ppt_generate_speaker_notes": ["ppt_generate_speaker_notes"],
    "generate_mindmap": ["generate_mindmap"],
    "generate_ppt": ["generate_ppt"],
    "ppt_generate_slides_with_pages": ["ppt_generate_slides_with_pages"],
    "ppt_apply_theme": ["ppt_apply_theme"],
    "ppt_apply_color": ["ppt_apply_color"],
}

api = Copilot(
    is_test=True,
    model_url="",
    wps_sid="",  # 账号 14701234567
    custom_headers={"X-Cc-Region": "feature3"},
    # custom_headers={"X-Cc-Region": "master"},
    search_engines="",
    agent="WPP",
)
from mangping.mangping_utils import chat_retry, r2qs
from renfangchao.cc_server.as_utils import split_string


def build_str(group_funcs):
    grouped_functions_str = ""
    for gf in group_funcs:
        functions_line = " ".join(gf)
        grouped_functions_str += f"{functions_line}\n"
    return grouped_functions_str[:-1] if grouped_functions_str else ""


def parse_assert(assert_str):
    expected_funcs_str = assert_str.strip()
    expected_funcs = []
    for line in expected_funcs_str.split("\n"):
        line = line.strip()
        if not line:
            continue
        funcs = line.split(" ")
        funcs = [f.strip() for f in funcs if f.strip()]
        expected_funcs.append(funcs)
    return expected_funcs


def find_first_difference(a, b):
    min_len = min(len(a), len(b))
    for i in range(min_len):
        if a[i] != b[i]:
            return b[i]
    if len(a) == len(b):
        return ""
    elif len(b) > len(a):
        return "多意图"
    else:
        return "少意图"


def judge(expected_funcs, grouped_functions, aim):

    is_passes = []
    one_result = aim[0] if aim else ""

    for i, ef in enumerate(expected_funcs):
        is_pass = False
        expect_str = " ".join(ef)
        if i < len(grouped_functions):
            code = " ".join(grouped_functions[i])
        else:
            code = ""
        if aim:
            if any([e in aim for e in ef]):
                is_pass = code == expect_str
                if not is_pass:
                    if i < len(grouped_functions):
                        one_result = find_first_difference(ef, grouped_functions[i])
                    else:
                        one_result = find_first_difference(ef, [])
            else:
                is_pass = True
        else:
            is_pass = code == expect_str

        is_passes.append(is_pass)
    is_all_pass = "pass" if all(is_passes) else "fail"
    return is_all_pass, one_result


def try_judge(expected_funcs, grouped_functions, aim):
    try:
        return judge(expected_funcs, grouped_functions, aim)
    except Exception as e:
        print(f"judge出错: {e}")
        return "fail", "报错"


def parse_code(resp):
    text, request_id = resp
    codes = []
    funcs = []
    errors = []
    next_is_error = False
    has_text = False
    is_ppt_outline_pages_ing = False
    is_ppt_generate_speaker_notes_ing = False
    for line in text.split("\n"):
        if line == "event:error":
            next_is_error = True
            continue
        if next_is_error:
            next_is_error = False
            errors.append(line)

        try:
            if line.startswith("data:"):
                ds = line[5:]
                if ds:
                    data = json.loads(ds)
                    # if data.get("type") == "code":
                    #     code = data["data"]
                    #     func = json.loads(code)["function"]
                    #     if func != "stop":
                    #         codes.append(code)
                    #         funcs.append(func)
                    if not data:
                        continue
                    if data.get("type") == "websearch":
                        content_websearch = {
                            "function": "websearch",
                            "query": data["data"]["query"],
                        }
                        codes.append(
                            json.dumps(content_websearch, ensure_ascii=False, indent=4)
                        )
                        funcs.append("websearch")
                    if data.get("type") == "mind_map_start":
                        codes.append('{"function":"generate_mindmap"}')
                        funcs.append("generate_mindmap")
                    if data.get("type") == "ppt_outline_start":
                        codes.append('{"function":"generate_ppt"}')
                        funcs.append("generate_ppt")
                    if data.get("type") == "text":
                        has_text = True
                    if data.get("type") == "image_start":
                        codes.append('{"function":"generate_image"}')
                        funcs.append("generate_image")
                    if data.get("type") == "generate_ppt":
                        codes.append('{"function":"generate_ppt"}')
                        funcs.append("generate_ppt")
                    if data.get("type") == "url_fetch":
                        content_url = {
                            "function": "url_fetch",
                            "url": data["data"]["url"],
                        }
                        codes.append(
                            json.dumps(content_url, ensure_ascii=False, indent=4)
                        )
                        funcs.append("url_fetch")
                    elif data.get("type") == "aidocs_search_start":
                        codes.append('{"function":"aidocs_search"}')
                        funcs.append("aidocs_search")
                    if data.get("type") == "ppt_outline_pages":
                        if not is_ppt_outline_pages_ing:
                            is_ppt_outline_pages_ing = True
                            codes.append(
                                '{"function":"ppt_generate_slides_with_pages"}'
                            )
                            funcs.append("ppt_generate_slides_with_pages")
                    else:
                        # 如果已经在处理ppt_outline_pages了，就不再添加
                        is_ppt_outline_pages_ing = False
                    if data.get("type") == "ppt_generate_speaker_notes_start":
                        codes.append('{"function":"ppt_generate_speaker_notes"}')
                        funcs.append("ppt_generate_speaker_notes")
                    if data.get("type") == "ppt_set_font_start":
                        codes.append('{"function":"ppt_set_font"}')
                        funcs.append("ppt_set_font")
        except Exception as e:
            print(f"处理history项时出错: {e}")
    if not codes and has_text:
        # 如果没有代码，但有文本，可能是因为没有生成代码
        codes.append('{"function":"chat"}')
        funcs.append("chat")
    return codes, funcs, errors, request_id


session_codes = {}
# 日志那边搞反了。。
sess_id = "请求ID"
req_id = "会话ID"
with open(
    r"D:\projects\llm_batch_master\logs\tool_calls_20250708_111218.jsonl", "r"
) as f:
    lines = f.readlines()
    for line in lines:
        data = json.loads(line)
        if data[sess_id] not in session_codes:
            session_codes[data[sess_id]] = ""
        code = json.dumps(json.loads(data["响应"]), ensure_ascii=False, indent=4)
        session_codes[data[sess_id]] += f"{data[req_id]} : {code}\n\n"
print(f"读取到 {len(session_codes)} 个会话的代码")
print(session_codes)


def run_one(self, row):
    session_id = row["session_id"].strip("'")

    codes = session_codes.get(session_id, "")
    if codes:
        airsheet.write_xl(
            [codes],
            f'{输出列编号}{row["row_index"]}',
            sheet_name=self.sheetname,
        )


if __name__ == "__main__":
    for sheetname in ss:
        print(f"开始处理 {sheetname} ...")
        ai = RunAi(
            file_id=file_id,
            sheetname=sheetname,
            must_have_columns=必须有的列名,
            skip_col_name=输出列名,
            clo_num_to_write=输出列编号,
            max_workers=10,
        )
        ai.run_one = MethodType(run_one, ai)
        ai.run()
    # c = api.history("8670977635057844")
    # print(c)

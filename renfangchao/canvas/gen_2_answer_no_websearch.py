import json
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from run_batch.run_ai import RunAi

file_id = "ck8qQ6zhTv5T"  # 文件
default_question_config = {"command_args": {"disable_websearch": True}}
# sheetname = "ppt"
必须有的列名 = ["问题"]
输出列名 = "session_id"  # 表示会跳过"答案"列已经有内容的行。
# 输出列名 = ""
输出列编号 = "I"  # 表示从把答案写到B列

ss = [
    "chat",
    "websearch",
    "generate_image",
    "ppt_set_animation",
    "ppt_set_font",
    "ppt_generate_speaker_notes",
    "generate_mindmap",
    "generate_ppt",
    "ppt_generate_slides_with_pages",
    # "ppt_apply_theme",
    # "ppt_apply_color",
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
    custom_headers={"X-Cc-Region": "feat_copilot_cc_multi_agents"},
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
                    if data.get("type") == "code":
                        code = data["data"]
                        func = json.loads(code)["function"]
                        if func != "stop":
                            codes.append(code)
                            funcs.append(func)
        except Exception as e:
            print(f"处理history项时出错: {e}")
    return codes, funcs, errors, request_id


def run_one(self, row):
    qs = r2qs(row)
    qs = [{**default_question_config, "question": q} for q in qs]
    fild_id = row["文件链接"].split("/")[-1].strip("")
    historys, rs, session_id = api.questions(questions=qs, context_file_id=fild_id, with_history=False)  # type: ignore
    session_id = str(session_id)
    results = [
        "'" + session_id,
        f"https://lingxi.wps.cn/chat/{session_id}",
    ]
    parsed_results = [parse_code(r) for r in rs]
    group_codes = [result[0] for result in parsed_results]
    group_funcs = [result[1] for result in parsed_results]
    errors = [result[2] for result in parsed_results]
    resuest_ids = [result[3] for result in parsed_results]
    resuest_ids_str = "\n".join(resuest_ids)
    errors_strs = []
    for i, error in enumerate(errors):
        if error:
            s = ";".join(error)
            errors_strs.append(f"{i + 1}: {s}\n")
        else:
            errors_strs.append("\n")
    error_str = "\n".join(errors_strs).strip()

    # print(555, group_funcs)
    grouped_functions_str = build_str(group_funcs)
    group_codes_str = build_str(group_codes)
    # print(111, json.dumps(grouped_functions_str))
    expected_funcs = parse_assert(row["调度断言"])
    # print(222, expected_funcs)
    # expected_funcs_str = build_str(expected_funcs)
    # print(3333, json.dumps(grouped_functions_str))
    results.append(grouped_functions_str)
    aim = aims[self.sheetname]
    is_pass, _ = try_judge(expected_funcs, group_funcs, [])
    is_aim_pass, one_result = try_judge(expected_funcs, group_funcs, aim)

    results.append(is_pass)
    results.append(is_aim_pass)
    results.append(one_result)
    results.append(group_codes_str)
    results.append(error_str)
    results.append(resuest_ids_str)
    airsheet.write_xl(
        results,
        f'{输出列编号}{row["row_index"]}',
        sheet_name=self.sheetname,
    )


if __name__ == "__main__":
    for sheetname in ss:
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

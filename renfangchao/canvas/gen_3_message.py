import json
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from run_batch.run_ai import RunAi

file_id = "cirOlZ8iwPYW"  # 文件
# sheetname = "ppt"
必须有的列名 = ["session_id"]
输出列名 = "codes"  # 表示会跳过"答案"列已经有内容的行。
# 输出列名 = ""
输出列编号 = "K"  # 表示从把答案写到B列

ss = [
    "ppt-chat",
    "ppt-websearch",
    "ppt-image",
    "ppt_set_animation",
    "ppt_set_font",
    "ppt_generate_speaker_notes",
    "ppt-mindmap",
    "ppt-generate_ppt",
    "ppt_generate_slides_with_pages",
    "ppt_apply_theme",
    "ppt_apply_color",
]

# ss = ["ppt_generate_speaker_notes"]
# ss = ss[:1]

api = Copilot(
    is_test=True,
    model_url="",
    wps_sid="",
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
    return grouped_functions_str.strip()


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


def run_one(self, row):
    session_id = row["session_id"]
    historys = api.history(session_id)
    group_funcs = {}
    # print(111, session_id, historys)
    for history in historys["data"]["list"]:
        if history["type"] == "code":
            # print(44444, history["content"])
            try:
                func = json.loads(history["content"])["function"]
                group_id = history.get("group_id", "default")
                group_funcs.setdefault(group_id, []).append(func)
            except Exception as e:
                print(f"处理history项时出错: {e}")

    group_funcs = list(group_funcs.values())
    # print(555, group_funcs)
    grouped_functions_str = build_str(group_funcs)
    # print(111, json.dumps(grouped_functions_str))
    expected_funcs = parse_assert(row["调度断言"])
    # print(222, expected_funcs)
    expected_funcs_str = build_str(expected_funcs)
    # print(3333, json.dumps(grouped_functions_str))
    results = []
    results.append(grouped_functions_str)
    is_pass = "pass" if grouped_functions_str == expected_funcs_str else "fail"
    results.append(is_pass)
    airsheet.write_xl(
        results,
        f'{输出列编号}{row["row_index"]}',
        sheet_name=self.sheetname,
    )


def run_one_try(self, row):
    try:
        run_one(self, row)
    except Exception as e:
        print(f"处理{row['row_index']}时出错: {e}")
        print(traceback.format_exc())
        airsheet.write_xl(
            ["error"],
            f'{输出列编号}{row["row_index"]}',
            sheet_name=self.sheetname,
        )


if __name__ == "__main__":
    for sheetname in ss:
        print(f"开始处理{sheetname}")
        ai = RunAi(
            file_id=file_id,
            sheetname=sheetname,
            must_have_columns=必须有的列名,
            skip_col_name=输出列名,
            clo_num_to_write=输出列编号,
            max_workers=20,
        )
        ai.run_one = MethodType(run_one_try, ai)
        ai.run()
    # c = api.history("8670977635057844")
    # print(c)

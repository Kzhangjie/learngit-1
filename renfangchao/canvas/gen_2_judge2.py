import json
import traceback
from types import MethodType

import airsheet
from copilot.api2_rfc import Copilot
from run_batch.run_ai import RunAi

file_id = "cirOlZ8iwPYW"  # 文件
sheetname = "ppt"
必须有的列名 = ["问题"]
输出列名 = ""  # 表示会跳过"答案"列已经有内容的行。

输出列编号 = "M"  # 表示从把答案写到B列

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
ss = ["ppt-image"]
aims = {
    "ppt-chat": ["chat"],
    "ppt-websearch": ["websearch"],
    "ppt-image": ["image"],
    "ppt_set_animation": ["ppt_set_animation"],
    "ppt_set_font": ["ppt_set_font"],
    "ppt_generate_speaker_notes": ["ppt_generate_speaker_notes"],
    "ppt-mindmap": ["generate_mindmap"],
    "ppt-generate_ppt": ["generate_ppt"],
    "ppt_generate_slides_with_pages": ["ppt_generate_slides_with_pages"],
    "ppt_apply_theme": ["ppt_apply_theme"],
    "ppt_apply_color": ["ppt_apply_color"],
}
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
    grouped_functions_str = row["codes"].split("\n")
    # print(111, json.dumps(grouped_functions_str))
    expected_funcs = parse_assert(row["调度断言"])
    # print(222, expected_funcs)
    is_passes = []
    aim = aims[self.sheetname]
    for i, ef in enumerate(expected_funcs):
        is_pass = False
        expect_str = " ".join(ef)
        if any([e in aim for e in ef]):
            if i < len(grouped_functions_str):
                code = grouped_functions_str[i]
            else:
                code = ""
            is_pass = code == expect_str
        else:
            is_pass = True

        is_passes.append(is_pass)
    is_pass = "pass" if all(is_passes) else "fail"
    results = [is_pass]
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
            max_workers=6,
        )
        ai.run_one = MethodType(run_one, ai)
        ai.run()
    # c = api.history("8670977635057844")
    # print(c)

from types import MethodType
from run_batch.run_code import RunCode
from run_batch.run_ai import RunAi
import airsheet
import traceback
import json
import re

file_id = "ctI6Ti36VX9x"  # 文件
sheetname = "wry-temp"
列名 = "planner_clean"
必须有的列名 = [f"{列名}1"]
输出列名 = ""  # 表示会跳过"答案"列已经有内容的行。
输出列编号 = ["BT", "BX"]  # 表示从把答案写到B列

minimax列名 = "minimax_clean"
from renfangchao.cc_server.as_utils import split_string, get_long_text

from deepdiff import DeepDiff


def run_one(self, row):
    try:
        planner = get_long_text(row, 列名)
        minimax = get_long_text(row, minimax列名)
        snap_planner = get_long_text(row, f"snap_{列名}")
        snap_minimax = get_long_text(row, f"snap_{minimax列名}")
        diff_planner = DeepDiff(snap_planner, planner)
        diff_minimax = DeepDiff(snap_minimax, minimax)
        success_planner = "通过" if diff_planner == {} else "不通过"
        success_minimax = "通过" if diff_minimax == {} else "不通过"
        diff_planner_text = (
            diff_planner.get("values_changed", {}).get("root", {}).get("diff", "")
        )

        diff_minimax_text = (
            diff_minimax.get("values_changed", {}).get("root", {}).get("diff", "")
        )

        r1 = [success_planner, *split_string(diff_planner_text)]

        r2 = [success_minimax, *split_string(diff_minimax_text)]
        airsheet.write_xl(
            r1, f"{输出列编号[0]}{row['row_index']}", sheet_name=sheetname
        )
        airsheet.write_xl(
            r2, f"{输出列编号[1]}{row['row_index']}", sheet_name=sheetname
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

import pandas

import airsheet
from renfangchao.verify.file_operations import copy_file
from renfangchao.verify.gen_1_answer import run_batch_verification
from renfangchao.verify.send_report import send_report
from run_batch.as_utils import get_df


def copy_failed_cases(file_id):
    """生成重试数据"""
    sheet_names = ["thinking_disabled", "thinking_enabled"]

    dfs = []
    for sheet_name in sheet_names:
        df = get_df(file_id, sheet_name, drop_na=False)
        df = df[df["是否通过"] != "pass"]
        print(f"Processing sheet: {sheet_name}, rows: {df.shape[0]}")
        print(df)
        dfs.append(df)
    # 把dfs合并为一个df
    if len(dfs) > 1:
        df = pandas.concat(dfs, ignore_index=True)
    else:
        df = dfs[0]
    # 去掉序号列
    df = df.reset_index(drop=True)
    # 第17列和之后的列，都设置为“”
    for col in df.columns[17:]:
        df[col] = ""

    airsheet.write_xl(df, "A1", sheet_name="重试")


if __name__ == "__main__":
    copy_failed_cases("440164870306")

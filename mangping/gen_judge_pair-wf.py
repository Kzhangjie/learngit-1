import sys
import json
import airsheet
import pandas as pd
from run_batch.as_utils import get_df
from itertools import combinations

file_id = "ctar6frjyjxP"
# 如果评判到一半，需要新增用例，可以新增一个场景，保持顺序
from_sheets = ["盲评题目"]
to_sheet = "盲评记录"
# 模型名，需要是列名的一部分
answer_cols = ["shangtang", "v3"]
df_list = []
for fs in from_sheets:
    temp_df = get_df(file_id=file_id, sheet_name=fs, drop_na=False)
    temp_df = temp_df[temp_df["问题"] != ""]  # type: ignore
    temp_df["场景"] = fs
    combinations_list = list(combinations(answer_cols, 2))
    # 遍历每个组合并创建单独的DataFrame
    for col1, col2 in combinations_list:
        temp_combined_df = temp_df[["场景", "编号", "问题", "文件内容"]].copy()
        temp_combined_df["模型A"] = col1  # 添加模型A列
        temp_combined_df["模型B"] = col2  # 添加模型B列
        temp_combined_df["理由A"] = temp_df[f"{col1}_reason"]
        temp_combined_df["答案A"] = temp_df[f"{col1}_answer"]
        temp_combined_df["理由B"] = temp_df[f"{col2}_reason"]
        temp_combined_df["答案B"] = temp_df[f"{col2}_answer"]
        df_list.append(temp_combined_df)

# 将所有DataFrame拼接成一个大的DataFrame
combined_df = pd.concat(
    df_list, keys=range(1, len(df_list) + 1), names=["组合ID", "原始索引"]
)
combined_df.reset_index(level="原始索引", drop=True, inplace=True)

# 设置新的索引ID
combined_df.reset_index(inplace=True)
combined_df.index += 1
combined_df.index.name = "ID"

print(combined_df.head())
print(len(combined_df))
airsheet.write_xl(combined_df, "A1", sheet_name=to_sheet)
head = ["ip", "用户名", "盲评结果", "盲评理由", "说明", "显示的答案A", "显示的答案B"]
airsheet.write_xl(head, "L1", sheet_name=to_sheet)

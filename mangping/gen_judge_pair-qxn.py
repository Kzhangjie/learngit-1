import sys
import json
import airsheet
from run_batch.as_utils import get_df
from itertools import combinations

file_id = "chdnOzKQZm9Y"
from_sheets = ["搜索总结测评","搜索总结测评 (模态卡)"]
to_sheet = "盲评记录"
# 模型名，需要是列名的一部分
answer_cols = ["kuake", "bocha"]
# answer_cols = ["doubao", "r1"]

combinations_list = list(combinations(answer_cols, 2))  # 将组合提前计算

all_records = []
combination_id = 0

for fs in from_sheets:
    # 获取数据并转换为列表
    rows = get_df(file_id=file_id, sheet_name=fs, drop_na=False).to_dict(
        orient="records"
    )
    for col1, col2 in combinations_list:  # 先遍历组合，再遍历行
        combination_id += 1
        for row in rows:
            if not row.get("问题", "").strip():
                continue
            row["场景"] = fs
            ansA = row.get(f"{col1}_answer")
            ansB = row.get(f"{col2}_answer")
            if ansA is None or ansB is None:
                continue
            if not ansA.strip() or not ansB.strip():
                continue
            new_record = {
                "组合ID": combination_id,
                "场景": row["场景"],
                "编号": row.get("编号"),
                "问题": row["问题"],
                "文件内容": row.get("文件内容"),
                "模型A": col1,
                "模型B": col2,
                "理由A": row.get(f"{col1}_reason"),
                "答案A": ansA,
                "理由B": row.get(f"{col2}_reason"),
                "答案B": ansB,
            }
            all_records.append(new_record)

print(all_records[:5])
print(len(all_records))
# 将 all_records 转换为 DataFrame
import pandas as pd

combined_df = pd.DataFrame(all_records)
airsheet.write_xl(combined_df, "A1", sheet_name=to_sheet)
head = ["ip", "用户名", "盲评结果", "盲评理由", "说明", "显示的答案A", "显示的答案B"]
airsheet.write_xl(head, "L1", sheet_name=to_sheet)

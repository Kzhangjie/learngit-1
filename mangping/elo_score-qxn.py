import pandas as pd
from utils.glicko2 import Player

import numpy as np
from run_batch.as_utils import get_df

file_id = "chdnOzKQZm9Y"
df = get_df(file_id, "盲评记录")
for col in ["问题", "答案A", "答案B"]:
    df = df.dropna(subset=[col])  # type: ignore
models_a = df["模型A"].unique()  # type: ignore
models_b = df["模型B"].unique()  # type: ignore
models = np.union1d(models_a, models_b)
print("所有模型", models)
scenes = df["场景"].unique()  # type: ignore

clo = "盲评结果"
base_model = "kuake"


def score(df):
    players = {name: Player(1500) for name in models}
    model_datas = {name: {"ratings": [], "rds": [], "outcomes": []} for name in models}
    for row in df.to_dict(orient="records"):
        player_a = players[row["模型A"]]
        player_b = players[row["模型B"]]
        data_a = model_datas[row["模型A"]]
        data_b = model_datas[row["模型B"]]
        if row[clo] == "答案A":
            outcomes_a, outcomes_b = 1, 0
        elif row[clo] == "答案B":
            outcomes_a, outcomes_b = 0, 1  # B wins
        elif row[clo] == "平局":
            outcomes_a, outcomes_b = 0.5, 0.5  # Draw
        else:
            continue
        data_a["ratings"].append(player_b.rating)
        data_a["rds"].append(player_b.rd)
        data_a["outcomes"].append(outcomes_a)

        data_b["ratings"].append(player_a.rating)
        data_b["rds"].append(player_a.rd)
        data_b["outcomes"].append(outcomes_b)
    for model_name, data in model_datas.items():
        if data["ratings"]:  # 确保有比赛数据
            # print(model_name,data["outcomes"])
            players[model_name].update_player(
                data["ratings"], data["rds"], data["outcomes"]
            )
    model_score = {}
    for model in models:
        print(
            f"{model}: Rating={players[model].getRating():.2f}, RD={players[model].getRd():.2f}"
        )

        model_score[model] = players[model].getRating()
    model_score_modify = {}
    for model in models:
        model_score_modify[model] = model_score[model] - model_score[base_model] + 1000
    return model_score_modify


def scores(df):
    dfs = {scene: df[df["场景"] == scene] for scene in scenes}
    dfs["所有"] = df
    datas = []
    for scene, df0 in dfs.items():
        # print(f"scene:{scene}")
        model_score = score(df0)
        model_score["场景"] = scene
        datas.append(model_score)
    return datas


import airsheet

if __name__ == "__main__":
    datas = scores(df)
    df = pd.DataFrame(datas)
    col_order = ["场景"] + [col for col in df.columns if col != "场景"]
    df = df[col_order]
    all_row = df[df["场景"] == "所有"].iloc[0]
    sorted_columns = df.drop("场景", axis=1).columns[(-all_row[1:]).argsort()]  # type: ignore
    sorted_df = df[["场景"] + sorted_columns.tolist()]
    empty_data = [["" for _ in range(5)] for _ in range(5)]
    airsheet.write_xl(empty_data, f"A1", sheet_name="统计")
    airsheet.write_xl(sorted_df, f"A1", sheet_name="统计")

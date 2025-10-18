# TwoReady--副程序
# 主要实现：单轮多轮情况分析，chat/websearch分发情况
import json
import sqlite3
from collections import Counter

import pandas as pd

DB_PATH = "dialog_data.db"
CLEANED_TABLE = "Clean_Data"
MINI_TABLE = "Mini_all_Data"


def get_connection():
    return sqlite3.connect(DB_PATH)


def is_mini_search_command(data_str):
    try:
        return json.loads(data_str).get("command") == "mini_search"
    except:
        return False


def extract_mini_search_sessions():
    conn = get_connection()
    if (
        MINI_TABLE
        in pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)[
            "name"
        ].values
    ):
        df_all = pd.read_sql_query(f"SELECT * FROM {MINI_TABLE}", conn)
    else:
        df_clean = pd.read_sql_query(f"SELECT * FROM {CLEANED_TABLE}", conn)
        df_clean["origin_data"] = df_clean["origin_data"].astype(str)
        df_user = df_clean[df_clean["Role"] == "user"].copy()
        df_user["is_mini"] = df_user["origin_data"].apply(is_mini_search_command)
        mini_ids = df_user[df_user["is_mini"]]["SessionID"].unique()
        df_all = df_clean[df_clean["SessionID"].isin(mini_ids)].copy()
        df_all.to_sql(MINI_TABLE, conn, if_exists="replace", index=False)
    conn.close()
    return df_all


def classify_dialog_turns(df_all):
    df_user = df_all[df_all["Role"] == "user"]
    session_turns = df_user.groupby("SessionID").size().reset_index(name="user_turns")
    session_turns["type"] = session_turns["user_turns"].apply(
        lambda x: "单轮" if x == 1 else "多轮"
    )
    return session_turns


def analyze_second_assistant_type(df_all):
    # 按 SessionID 和 Timestamp 排序
    sort_cols = ["SessionID"]
    if "Timestamp" in df_all.columns:
        sort_cols.append("Timestamp")
    df_all = df_all.sort_values(by=sort_cols).reset_index(drop=True)

    result = []

    for session_id, group in df_all.groupby("SessionID"):
        group = group.reset_index(drop=True)
        for i in range(len(group)):
            if group.loc[i, "Role"] == "assistant" and group.loc[i, "Type"] == "code":
                content = group.loc[i, "Content"]
                try:
                    content_json = json.loads(content)
                    function_value = content_json.get("function", "")
                    if function_value == "chat" or function_value == "":
                        result.append("chat")
                    elif function_value == "websearch":
                        result.append("websearch")
                    else:
                        result.append("其他")
                except (json.JSONDecodeError, TypeError):
                    result.append("其他")  # 内容不是合法 JSON 或为空

    # 汇总计数
    counts = Counter(result)
    return {
        "chat": counts.get("chat", 0),
        "websearch": counts.get("websearch", 0),
        "其他": counts.get("其他", 0),
    }, result

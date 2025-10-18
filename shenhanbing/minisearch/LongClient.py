# LongClient.py--副程序
# 主要实现：划词的长度分析、用户使用平台分析
import json
import sqlite3

import pandas as pd

DB_PATH = "dialog_data.db"
MINI_TABLE_USER = "mini_data_user"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_data(table, columns):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT {', '.join(columns)} FROM {table}", conn)
    conn.close()
    return df


def extract_valid_client_type(data_str):
    try:
        data_dict = json.loads(data_str)
        return data_dict.get("client_type", "").strip() or None
    except Exception:
        return None


def analyze_length_distribution():
    df = get_data(MINI_TABLE_USER, ["SessionID", "Content"])
    df["length"] = df["Content"].fillna("").str.len()
    df["length_category"] = pd.cut(
        df["length"],
        bins=[0, 10, 100, 500, 1000, 3000, float("inf")],
        labels=[
            "1-10个字符",
            "11-100个字符",
            "101-500个字符",
            "501-1000个字符",
            "1001-3000个字符",
            "3000字符以上",
        ],
        right=True,
    )
    return (
        df["length_category"]
        .value_counts()
        .sort_index()
        .reset_index(name="count")
        .rename(columns={"index": "length_category"})
    )


def analyze_client_type():
    df = get_data(MINI_TABLE_USER, ["SessionID", "origin_data"])
    df["client_type"] = df["origin_data"].astype(str).apply(extract_valid_client_type)
    valid = df[df["client_type"].notna()]
    invalid = df[df["client_type"].isna()]
    return (
        valid["client_type"]
        .value_counts()
        .reset_index(name="count")
        .rename(columns={"index": "client_type"}),
        valid,
        invalid,
    )

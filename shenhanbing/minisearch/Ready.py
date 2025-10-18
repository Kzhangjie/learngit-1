# Ready.py--副程序
# 主要实现：数据库搭建、数据表生成，数据清洗
import json
import re
import sqlite3
import unicodedata

import chardet
import pandas as pd

INPUT_FILE = "fuben.csv"
DB_PATH = "dialog_data.db"
ORIGINAL_TABLE = "dialog_data"
CLEANED_TABLE = "Clean_Data"
MINI_TABLE_USER = "mini_data_user"
EXCEL_EXPORT_FILE = "用户输入异常情况.xlsx"


def get_connection():
    return sqlite3.connect(DB_PATH)


def detect_encoding(file_path):
    with open(file_path, "rb") as f:
        rawdata = f.read(100000)
        result = chardet.detect(rawdata)
        print(f"检测到文件编码为: {result['encoding']}")
        return result["encoding"]


def is_invalid_user_input(content):
    if not isinstance(content, str):
        return True
    cleaned = re.sub(r"[\s\u3000]+", "", content)
    if not cleaned:
        return True
    for char in cleaned:
        if not unicodedata.category(char).startswith(("C", "Z")):
            return False
    return True


def is_mini_search_command(data_str):
    try:
        data = json.loads(data_str)
        return data.get("command") == "mini_search"
    except (json.JSONDecodeError, TypeError):
        return False


def import_csv_to_db():
    encoding = detect_encoding(INPUT_FILE)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {ORIGINAL_TABLE} (
        SessionID TEXT, SessionStatus TEXT, CreatorID TEXT,
        SessionCreateTime TEXT, CompanyID TEXT, SessionTitle TEXT,
        MessageID TEXT, Content TEXT, Role TEXT, Type TEXT,
        MessageStatus TEXT, GroupID TEXT, MessageCreateTime TEXT,
        origin_data TEXT
    )"""
    )
    cursor.execute(f"DELETE FROM {ORIGINAL_TABLE}")

    with open(INPUT_FILE, "r", encoding=encoding) as f:
        first_line = f.readline().strip()
        csv_columns = first_line.split(",")

    insert_query = f"""
    INSERT INTO {ORIGINAL_TABLE} ({', '.join(csv_columns)})
    VALUES ({', '.join(['?'] * len(csv_columns))})
    """

    chunksize = 100000
    imported_rows = skipped_rows = error_rows = 0

    try:
        for i, chunk in enumerate(
            pd.read_csv(
                INPUT_FILE, encoding=encoding, chunksize=chunksize, on_bad_lines="skip"
            )
        ):
            for row_idx, row in chunk.iterrows():
                try:
                    values = tuple(None if pd.isna(val) else val for val in row)
                    cursor.execute(insert_query, values)
                    imported_rows += 1
                except sqlite3.IntegrityError:
                    skipped_rows += 1
                except Exception:
                    error_rows += 1
                if imported_rows % 1000 == 0:
                    conn.commit()
        conn.commit()
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        conn.rollback()
    finally:
        conn.close()


def clean_invalid_user_input():
    conn = get_connection()
    df_all = pd.read_sql_query(f"SELECT * FROM {ORIGINAL_TABLE}", conn)
    df_user = df_all[df_all["Role"] == "user"].copy()
    df_user["is_abnormal"] = df_user["Content"].apply(is_invalid_user_input)
    df_abnormal = df_user[df_user["is_abnormal"]]
    abnormal_sids = df_abnormal["SessionID"].unique().tolist()

    df_abnormal[["SessionID", "Content"]].drop_duplicates().to_excel(
        EXCEL_EXPORT_FILE, index=False
    )
    df_clean = df_all[~df_all["SessionID"].isin(abnormal_sids)]
    df_clean.to_sql(CLEANED_TABLE, conn, if_exists="replace", index=False)
    conn.close()


def extract_mini_search_command():
    conn = get_connection()
    df_clean = pd.read_sql_query(f"SELECT * FROM {CLEANED_TABLE}", conn)
    df_clean["origin_data"] = df_clean["origin_data"].astype(str)
    df_user = df_clean[df_clean["Role"] == "user"].copy()
    df_user_mini = df_user[df_user["origin_data"].apply(is_mini_search_command)]
    df_user_mini.to_sql(MINI_TABLE_USER, conn, if_exists="replace", index=False)
    conn.close()


def run_all():
    import_csv_to_db()
    clean_invalid_user_input()
    extract_mini_search_command()

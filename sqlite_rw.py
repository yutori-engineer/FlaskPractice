import sqlite3
import pandas as pd
import re
import traceback
from datetime import datetime
from logger_config import setup_logger

logger = setup_logger(__name__)


# --- SQLiteユーティリティ関数 ---
def get_existing_columns(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    return {info[1] for info in cursor.fetchall()}

def infer_sqlite_type(dtype) -> str:
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_float_dtype(dtype):
        return "REAL"
    elif pd.api.types.is_bool_dtype(dtype):
        return "INTEGER"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "TEXT"
    else:
        return "TEXT"


def add_column_if_not_exists(conn, table_name, column_name, column_type):
    try:
        existing_columns = get_existing_columns(conn, table_name)
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
            logger.info(f"カラム '{column_name}' を '{table_name}' に追加しました。")
    except Exception:
        logger.error("カラム追加中にエラー:\n%s", traceback.format_exc())


def add_missing_columns(df, conn, table_name):
    existing_columns = get_existing_columns(conn, table_name)
    missing_columns = set(df.columns) - existing_columns

    for col in missing_columns:
        col_type = infer_sqlite_type(df[col].dtype)
        try:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type};")
            logger.info(f"カラム '{col}' を '{table_name}' に追加しました。")
        except Exception:
            logger.error(f"カラム '{col}' の追加に失敗:\n%s", traceback.format_exc())


# --- データ書き込み関数 ---
def to_sqlite(df, db_path, table_name, symbol='', if_exists='append'):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            df = df.reset_index()
            add_missing_columns(df, conn, table_name)
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            logger.info(f"データ '{symbol}' を SQLite '{db_path}' の '{table_name}' に保存しました。")
    except sqlite3.OperationalError as e:
        handle_sqlite_operational_error(e, df, db_path, table_name, symbol, if_exists)
    except Exception:
        logger.error("データ書き込み中にエラーが発生しました（symbol='%s'）:\n%s", symbol, traceback.format_exc())


def handle_sqlite_operational_error(e, df, db_path, table_name, symbol, if_exists):
    error_msg = str(e)
    match = re.search(r'table (\w+) has no column named (\w+)', error_msg)
    if match:
        table, column = match.groups()
        if column in df.columns:
            column_type = infer_sqlite_type(df[column].dtype)
            logger.warning(f"カラム '{column}' が存在しないため '{column_type}' 型で追加します。")
            with sqlite3.connect(db_path) as conn:
                add_column_if_not_exists(conn, table, column, column_type)

            # 再試行
            try:
                with sqlite3.connect(db_path, timeout=10) as conn:
                    df = df.reset_index()
                    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
                    logger.info(f"再試行成功: データ '{symbol}' を SQLite に保存しました。")
            except Exception:
                logger.error("再試行中にエラー発生（symbol='%s'）:\n%s", symbol, traceback.format_exc())
        else:
            logger.error(f"エラーで指定されたカラム '{column}' が DataFrame に存在しません。")
    else:
        logger.error("未対応の OperationalError:\n%s", traceback.format_exc())


# --- データ読み込み関数 ---
def read_sqlite(db_path, table_name, symbol=None, query=None):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            if query is None:
                query = f"SELECT * FROM {table_name}"
                if symbol:
                    query += " WHERE symbol = ?"
                    df = pd.read_sql_query(query, conn, params=(f"{symbol}.T",))
                else:
                    df = pd.read_sql_query(query, conn)
            else:
                df = pd.read_sql_query(query, conn)

            logger.info(f"'{table_name}' からデータを読み込みました。")
            return df
    except Exception:
        logger.error("データ読み込み中にエラー:\n%s", traceback.format_exc())
        return pd.DataFrame()


# --- 実行例 ---
if __name__ == '__main__':
    db_path = "./stock_data.db"
    symbol = '6758'
    table_name = 'stock_history_1d'

    start_time = datetime.now()
    df = read_sqlite(db_path, table_name, symbol).reset_index()
    df.set_index(['symbol', 'date'], inplace=True)
    print(df)
    end_time = datetime.now()

    print(f"処理時間: {end_time - start_time}")

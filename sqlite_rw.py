import sqlite3
import pandas as pd
import re
import logging
import traceback
import datetime

# --- ログ設定（ファイル + コンソール） ---
logger = logging.getLogger(__name__)
LOG_LEVEL = logging.INFO  # または logging.DEBUG にすると詳細ログも出る
logger.setLevel(LOG_LEVEL)

# ファイルハンドラ（ログファイルに出力）
file_handler = logging.FileHandler('./error.txt', encoding='utf-8')
file_handler.setLevel(LOG_LEVEL)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

# コンソールハンドラ（標準出力に出力）
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(file_formatter)

# 既存のハンドラが重複して追加されないようにする
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# --- カラム追加関数 ---
def add_column_if_not_exists(db_path, table_name, column_name, column_type):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [info[1] for info in cursor.fetchall()]
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
                conn.commit()
                logger.info(f"カラム '{column_name}' をテーブル '{table_name}' に追加しました。")
    except Exception:
        logger.error("カラム追加中にエラーが発生しました:\n%s", traceback.format_exc())

def infer_sqlite_type(dtype) -> str:
    """
    pandas の dtype から SQLite 用の型を推定する
    """
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
    
def add_missing_columns(df, db_path, table_name):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        existing_columns = {info[1] for info in cursor.fetchall()}
        missing_columns = set(df.columns) - existing_columns
        for col in missing_columns:
            col_type = infer_sqlite_type(df[col].dtype)
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type};")
                logger.info(f"カラム '{col}' を追加しました。")
            except Exception:
                logger.error(f"カラム '{col}' の追加に失敗しました:\n{traceback.format_exc()}")
        conn.commit()
        
def to_sqlite(df, db_path, table_name, symbol='', if_exists='append'):
    add_missing_columns(df, db_path, table_name)
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            df=df.reset_index()
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            print(f"データ'{symbol}'がSQLiteデータベース '{db_path}' のテーブル '{table_name}' に保存されました。")
    except sqlite3.OperationalError as e:
        error_msg = str(e)
        match = re.search(r'table (\w+) has no column named (\w+)', error_msg)
        if match:
            table, column = match.groups()
            # 型をdfから推論
            if column in df.columns:
                column_type = infer_sqlite_type(df[column].dtype)
                logger.warning(f"カラム '{column}' が存在しないため '{column_type}' 型で追加を試みます。")
                add_column_if_not_exists(db_path, table, column, column_type)
            else:
                logger.error(f"エラーに示されたカラム '{column}' がDataFrameに存在しません。")
                return

            # 再実行
            try:
                with sqlite3.connect(db_path, timeout=10) as conn:
                    df=df.reset_index()
                    df.to_sql(table_name, conn, if_exists=if_exists, index=False)
                    print(f"再試行成功: データ'{symbol}'がSQLiteデータベース '{db_path}' に保存されました。")
            except Exception:
                logger.error("データ書き込み再試行中にエラーが発生しました（symbol='%s'）:\n%s", symbol, traceback.format_exc())
        else:
            logger.error("データ書き込み中に未対応のエラーが発生しました（symbol='%s'）:\n%s", symbol, traceback.format_exc())
    except Exception:
        logger.error("データ書き込み中にエラーが発生しました（symbol='%s'）:\n%s", symbol, traceback.format_exc())

# --- データ読み込み関数 ---
def read_sqlite(db_path, table_name, symbol=None, query=None):
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            if query is None and symbol:
                query = f"SELECT * FROM {table_name} WHERE symbol = ?"
                df = pd.read_sql_query(query, conn, params=(f"{symbol}.T",))
            else:
                if query is None:
                    query = f"SELECT * FROM {table_name}"
                df = pd.read_sql_query(query, conn)

            print(f"データをSQLiteデータベース '{db_path}' のテーブル '{table_name}' から読み込みました。")
            return df
    except Exception:
        logger.error("データ読み込み中にエラーが発生しました:\n%s", traceback.format_exc())
        return pd.DataFrame()

if __name__ == '__main__':
            # SQLiteデータベースのパス
    db_path = ".\stock_data.db"
    symbol = '1301'
    table_name = 'stock_history_1d'

    # start_time = datetime.datetime.now()
    # print(start_time)
    # 銘柄コードを取得して関数を実行
    df = read_sqlite(db_path, table_name, symbol).reset_index()
    df.set_index(['symbol', 'date'])
    print(df)
    
    # end_time = datetime.datetime.now()
    # print(end_time)
    
    # delta = end_time - start_time
    # print(delta)


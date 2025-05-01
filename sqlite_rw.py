import sqlite3
import pandas as pd
import logging
import traceback

# --- ログ設定（ファイル + コンソール） ---
logger = logging.getLogger('sqlite_logger')
logger.setLevel(logging.ERROR)  # 全体のログレベルを設定

# ファイルハンドラ（ログファイルに出力）
file_handler = logging.FileHandler('./error.txt', encoding='utf-8')
file_handler.setLevel(logging.ERROR)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)

# コンソールハンドラ（標準出力に出力）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
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
            
            # 既存のカラムを確認するクエリ
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 既にカラムが存在している場合は追加しない
            if column_name not in columns:
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                cursor.execute(alter_query)
                print(f"カラム '{column_name}' がテーブル '{table_name}' に追加されました。")
            else:
                print(f"カラム '{column_name}' は既にテーブル '{table_name}' に存在します。")
    
    except sqlite3.Error as e:
        print(f"エラーが発生しました: {e}")

# --- データ書き込み関数 ---
def to_sqlite(df, db_path, table_name, symbol='', if_exists='replace'):
    try:
        # 必要なカラムが存在しない場合に追加する処理
        # 例えば 'targetHighPrice' カラムを追加したい場合
        add_column_if_not_exists(db_path, table_name, 'targetHighPrice', 'REAL')
        
        with sqlite3.connect(db_path, timeout=10) as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=True)
            print(f"データ'{symbol}'がSQLiteデータベース '{db_path}' のテーブル '{table_name}' に保存されました。")
    
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

import sqlite3
import pandas as pd

def to_sqlite(df, db_path, table_name, symbol='',if_exists='replace'):
    #DataFrameをSQLiteデータベースに保存する。
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=True)
            print(f"データ'{symbol}'がSQLiteデータベース '{db_path}' のテーブル '{table_name}' に保存されました。")
    except Exception as e:
        print(f"データ書き込み中にエラーが発生しました: {e}")
        return pd.DataFrame()  # 空のDataFrameを返す

def read_sqlite(symbol, db_path, table_name):
    #DataFrameをSQLiteデータベースから読み込む。
    try:
        with sqlite3.connect(db_path, timeout=10) as conn:
            # クエリを実行してcodeに一致するレコードだけを抽出
            query = f"""
                SELECT *
                FROM {table_name}
                WHERE symbol = ?
            """
            df = pd.read_sql_query(query, conn, params=(f"{symbol}.T",))
            return df
            print(f"データをSQLiteデータベース '{db_path}' のテーブル '{table_name}' から読み込みました。")
    except Exception as e:
        print(f"データ読み込み中にエラーが発生しました: {e}")
        return pd.DataFrame()  # 空のDataFrameを返す
    
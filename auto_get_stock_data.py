import sqlite3
import pandas as pd
import datetime
from sqlite_rw import to_sqlite
from get_yahooquery import get_stock_history, get_all_financial_data, get_financial_data

def get_financials_for_all_codes(db_path):
    try:
        with sqlite3.connect(db_path) as conn:
            # 銘柄コードをすべて取得
            code_table = 'taishakumeigara'
            cursor = conn.execute(f'''
                SELECT 銘柄コード 
                FROM {code_table} 
                WHERE "信用区分" = "貸借銘柄" AND "市場区分/商品区分" IN ("プライム","スタンダード","グロース")
            ''')
            symbols = [row[0] for row in cursor.fetchall()]

        # 各銘柄ごとにデータ取得
        for symbol in symbols:
            df3 = get_financial_data(symbol)
            to_sqlite(df3, db_path, table_name='financial_data', symbol='', if_exists='append')

    except sqlite3.Error as e:
        print(f"SQLiteエラーが発生しました: {e}")

def get_stock_data_for_selected_codes(db_path):
    try:
        with sqlite3.connect(db_path) as conn:
            # 指定テーブルの中身をクリア（DELETE FROM）
            tables_to_clear = ['stock_history_1d', 'stock_history_5m', 'stock_history_1mo', 'all_financial_data']
            with conn:
                for table in tables_to_clear:
                    conn.execute(f"DELETE FROM {table}")
                    print(f"{table} のデータを削除しました。")

            # 選定された銘柄コードを取得
            code_table = 'financial_data'
            cursor = conn.execute(f'''
                SELECT substr(symbol, 1, 4)
                FROM financial_data AS fd
                WHERE date = (
                    SELECT MAX(date)
                    FROM {code_table} AS sub
                    WHERE sub.symbol = fd.symbol
                )
                AND targetHighPrice IS NOT NULL
                AND recommendationKey IN ('strong_buy', 'buy', 'underperform', 'sell')
            ''')
            symbols = [row[0] for row in cursor.fetchall()]

        # 各銘柄ごとにデータ取得
        for symbol in symbols:
            df = get_stock_history(symbol, period='1y', interval='1d')
            to_sqlite(df, db_path, table_name='stock_history_1d', symbol='', if_exists='append')

            df1 = get_stock_history(symbol, period='60d', interval='5m')
            to_sqlite(df1, db_path, table_name='stock_history_5m', symbol='', if_exists='append')

            df2 = get_stock_history(symbol, period='max', interval='1mo')
            to_sqlite(df2, db_path, table_name='stock_history_1mo', symbol='', if_exists='append')

            df4 = get_all_financial_data(symbol)
            to_sqlite(df4, db_path, table_name='all_financial_data', symbol='', if_exists='append')

    except sqlite3.Error as e:
        print(f"SQLiteエラーが発生しました: {e}")

if __name__ == '__main__':
    db_path = "./stock_data.db"

    start_time = datetime.datetime.now()
    print(start_time)

    get_financials_for_all_codes(db_path)
    get_stock_data_for_selected_codes(db_path)

    end_time = datetime.datetime.now()
    print(end_time)

    delta = end_time - start_time
    print(delta)

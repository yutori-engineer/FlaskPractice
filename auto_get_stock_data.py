import sqlite3
import datetime
from sqlite_rw import to_sqlite, read_sqlite
from get_yahooquery import get_stock_history, get_all_financial_data, get_financial_data

def get_financials_for_all_codes(db_path):

    try:
        with sqlite3.connect(db_path) as conn:
            # 銘柄コードをすべて取得
            with conn:
                code_table='taishakumeigara'
                cursor = conn.execute(f'SELECT 銘柄コード FROM {code_table} WHERE "市場区分/商品区分" != "ETF"  AND "信用区分" = "貸借銘柄"')
                codes = [row[0] for row in cursor.fetchall()]

            # 各銘柄ごとにデータ取得
            for code in codes:
                symbol = f"{code}.T"
                df = get_stock_history(symbol, period='1y', interval='1d')
                to_sqlite(df, db_path, table_name = 'stock_history_1d', symbol='',if_exists='replace')
                
                df1 = get_stock_history(symbol, period='60d', interval='5m')
                to_sqlite(df1, db_path, table_name = 'stock_history_5m', symbol='',if_exists='replace')
                
                df2 = get_stock_history(symbol, period='max', interval='1mo')
                to_sqlite(df2, db_path, table_name = 'stock_history_1mo', symbol='',if_exists='replace')
                
                df3 = get_financial_data(symbol)
                to_sqlite(df3, db_path, table_name = 'financial_data', symbol='',if_exists='replace')
                
                df4 = get_all_financial_data(symbol)
                to_sqlite(df4, db_path, table_name = 'all_financial_data', symbol='',if_exists='replace')
    except sqlite3.Error as e:
        print(f"SQLiteエラーが発生しました: {e}")

if __name__ == '__main__':
            # SQLiteデータベースのパス
    db_path = ".\stock_data.db"

    start_time = datetime.datetime.now()
    print(start_time)
    # 銘柄コードを取得して関数を実行
    get_financials_for_all_codes(db_path)
    
    end_time = datetime.datetime.now()
    print(end_time)
    
    delta = end_time - start_time
    print(delta)


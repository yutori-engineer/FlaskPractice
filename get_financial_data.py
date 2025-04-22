from yahooquery import Ticker
import pandas as pd
import sqlite3

#yahooqueryから株価データを取得する
def get_financial_data(code):
    ticker = Ticker(code + '.T')
    df = ticker.all_financial_data()

    # SQLiteデータベースに接続
    conn = sqlite3.connect('stock_data.db', timeout=10)
    # データベースに書き込み
    df.to_sql('financial_data', conn, if_exists='append', index=True)
    # データベース接続を閉じる
    conn.close()
    return (code)

if __name__ == '__main__':
    code = get_financial_data('2413')
    print(code)
    print('成功しました')


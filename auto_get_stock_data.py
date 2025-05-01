from yahooquery import Ticker
import sqlite3
import time
from requests.exceptions import ChunkedEncodingError
from urllib3.exceptions import ProtocolError
import datetime

#yahooqueryから株価データを取得する
def get_stock_data(code):
    max_retries = 3
    retry_delay = 2  # 秒

    for attempt in range(max_retries):
        try:
            ticker = Ticker(code + '.T')
            df = ticker.history(period='max', interval='1mo')
            return df
        except (ChunkedEncodingError, ProtocolError) as e:
            if attempt == max_retries - 1:  # 最後の試行の場合
                raise  # エラーを再度発生させる
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
            continue

def get_stock_codes_and_process(db_path):
    """
    SQLiteのテーブル 'taishakumeigara' から銘柄コードを取得し、
    各銘柄コードに対して関数 'process_stock_code' を繰り返し実行する。

    Parameters:
        db_path (str): SQLiteデータベースのパス。
    """
    try:
        # データベースに接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 銘柄コードを取得するSQLクエリ
        query = 'SELECT "銘柄コード" FROM taishakumeigara WHERE "市場区分/商品区分" != "ETF"  AND "信用区分" = "貸借銘柄"'
        cursor.execute(query)

        # 結果を1つずつ取得して関数に渡す
        for row in cursor.fetchall():
            stock_code = row[0]
            get_financial_price(stock_code)

        # 接続を閉じる
        conn.close()
        print("すべての銘柄コードを処理しました。")

    except sqlite3.Error as e:
        print(f"SQLiteエラーが発生しました: {e}")

if __name__ == '__main__':
            # SQLiteデータベースのパス
    db_path = ".\stock_data.db"

    start_time = datetime.datetime.now()
    print(start_time)
    # 銘柄コードを取得して関数を実行
    get_stock_codes_and_process(db_path)
    
    end_time = datetime.datetime.now()
    print(end_time)
    
    delta = end_time - start_time
    print(delta)


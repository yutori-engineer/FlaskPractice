from yahooquery import Ticker
import pandas as pd
import sqlite3
import time
from requests.exceptions import ChunkedEncodingError
from urllib3.exceptions import ProtocolError

#yahooqueryから株価データを取得する
def get_stock_data(code):
    max_retries = 3
    retry_delay = 2  # 秒

    for attempt in range(max_retries):
        try:
            ticker = Ticker(code + '.T')
            # ticker = Ticker(code)
            # df = ticker.history(period='60d', interval='5m') #5分足データは最大60日
            # df = ticker.history(period='7d', interval='1m') #1分足データは最大7日
            # df = ticker.history(period='3y', interval='1d')
            df = ticker.history(period='max', interval='1mo')
            
            #インデックスを解除   
            df = df.reset_index()
            # 日付データを datetime に変換し、インデックスとして設定
            df['date'] = pd.to_datetime(df['date'])
            df = df.rename(columns={
                'date': 'Date', 
                'symbol': 'Symbol'
            })
            df = df.set_index('Date')
            
            df = df.rename(columns={
                'open': 'Open', 
                'high': 'High', 
                'low': 'Low', 
                'close': 'Close', 
                'volume': 'Volume'
            })
            df['Under'] = df['Low'] - df['Open']
            df['Body'] = df['Close'] - df['Open']
            df['Over'] = df['High'] - df['Open']
            print(df)
            df.to_csv(f'C:/Users/Owner/Desktop/{code}.csv')
            
            # SQLiteデータベースに接続
            # conn = sqlite3.connect('stock_data.db', timeout=10)
            # # データベースに書き込み
            # df.to_sql('historical_price', conn, if_exists='append', index=True) #全銘柄の価格データベース
            # # df.to_sql('stock_data_' + code, conn, if_exists='replace', index=True) #銘柄ごとにデータベースを分ける場合
            # # データベース接続を閉じる
            # conn.close()
            return (code)
        except (ChunkedEncodingError, ProtocolError) as e:
            if attempt == max_retries - 1:  # 最後の試行の場合
                raise  # エラーを再度発生させる
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
            continue

if __name__ == '__main__':
    code = get_stock_data('7201') # 日経225取得'^N225'
    print(code)
    print('成功しました')


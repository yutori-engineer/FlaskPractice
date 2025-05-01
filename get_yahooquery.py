from yahooquery import Ticker
import pandas as pd
from datetime import date
from requests.exceptions import ChunkedEncodingError
from urllib3.exceptions import ProtocolError
import time

def get_stock_history(symbol, period='1y', interval='1d'):
    max_retries = 3
    retry_delay = 2  # 秒

    for attempt in range(max_retries):
        try:
            ticker = Ticker(symbol + '.T')
            df = ticker.history(period=period, interval=interval)

            # --- 移動平均線の計算 ---
            df["MA5"] = df["close"].rolling(window=5).mean()
            df["MA20"] = df["close"].rolling(window=20).mean()
            df["MA60"] = df["close"].rolling(window=60).mean()
            print(f"{symbol}の株価時系列{interval}取得しました。")  
            return df
        
        except (ChunkedEncodingError, ProtocolError) as e:
            if attempt == max_retries - 1:  # 最後の試行の場合
                raise  # エラーを再度発生させる
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
            continue
        
        except Exception as e:
            print(f"データ取得時にエラーが発生しました: {e}{symbol}")
            return pd.DataFrame() 
    
def get_financial_data(symbol):
    max_retries = 3
    retry_delay = 2  # 秒

    for attempt in range(max_retries):
        try:
            ticker = Ticker(symbol + '.T')
            financial_data = ticker.financial_data
            
            # 辞書のキーを取得
            keys = list(financial_data.keys())
            if not keys:
                return None
                
            # 最初の銘柄のデータを取得
            first_symbol = keys[0]
            data = financial_data[first_symbol]   
            # DataFrameを作成
            df = pd.DataFrame([data])
            df["symbol"] = first_symbol
            df["date"] = date.today().strftime('%Y-%m-%d')
            # symbolとdateをインデックスに設定（MultiIndex）
            df = df.set_index(['symbol', 'date'])     
            print(f"{symbol}の株価KPIデータ取得しました。")  
            return df
        
        except (ChunkedEncodingError, ProtocolError) as e:
            if attempt == max_retries - 1:  # 最後の試行の場合
                raise  # エラーを再度発生させる
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
            continue
        
        except Exception as e:
            print(f"データ取得時にエラーが発生しました: {e}{symbol}")
            return pd.DataFrame() 

def get_all_financial_data(symbol):
    max_retries = 3
    retry_delay = 2  # 秒

    for attempt in range(max_retries):
        try:
            ticker = Ticker(symbol + '.T')
            df = ticker.all_financial_data()
            df = df.reset_index()
            df = df.set_index(['symbol', 'asOfDate'])  
            
            print(f"{symbol}の財務データ取得しました。")  
            return df
        
        except (ChunkedEncodingError, ProtocolError) as e:
            if attempt == max_retries - 1:  # 最後の試行の場合
                raise  # エラーを再度発生させる
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
            continue
        except Exception as e:
            print(f"データ取得時にエラーが発生しました: {e}{symbol}")
            return pd.DataFrame() 
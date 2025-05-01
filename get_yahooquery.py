import logging
import sqlite3
import pandas as pd
import time
from datetime import date
from yahooquery import Ticker
from requests.exceptions import ChunkedEncodingError
from urllib3.exceptions import ProtocolError
import traceback

# --- ログ設定（ファイル + コンソール） ---
logger = logging.getLogger('stock_logger')
logger.setLevel(logging.ERROR)

# ファイル出力
file_handler = logging.FileHandler('./error.txt', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S'))

# コンソール出力
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S'))

# 重複追加を防止
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_stock_history(symbol, period='1y', interval='1d'):
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            ticker = Ticker(symbol + '.T')
            df = ticker.history(period=period, interval=interval)

            df["MA5"] = df["close"].rolling(window=5).mean()
            df["MA20"] = df["close"].rolling(window=20).mean()
            df["MA60"] = df["close"].rolling(window=60).mean()
            print(f"{symbol}の株価時系列{interval}取得しました。")  
            return df

        except (ChunkedEncodingError, ProtocolError):
            if attempt == max_retries - 1:
                logger.error(f"{symbol} の株価データ取得で接続エラー（最終試行失敗）:\n%s", traceback.format_exc())
                raise
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)

        except Exception:
            logger.error(f"{symbol} の株価データ取得中にエラー:\n%s", traceback.format_exc())
            return pd.DataFrame()

def get_financial_data(symbol):
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            ticker = Ticker(symbol + '.T')
            financial_data = ticker.financial_data

            keys = list(financial_data.keys())
            if not keys:
                return None

            first_symbol = keys[0]
            data = financial_data[first_symbol]
            df = pd.DataFrame([data])
            df["symbol"] = first_symbol
            df["date"] = date.today().strftime('%Y-%m-%d')
            df = df.set_index(['symbol', 'date'])

            print(f"{symbol}の株価KPIデータ取得しました。")
            return df

        except (ChunkedEncodingError, ProtocolError):
            if attempt == max_retries - 1:
                logger.error(f"{symbol} のKPIデータ取得で接続エラー（最終試行失敗）:\n%s", traceback.format_exc())
                raise
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)

        except Exception:
            logger.error(f"{symbol} のKPIデータ取得中にエラー:\n%s", traceback.format_exc())
            return pd.DataFrame()
        
def get_all_financial_data(symbol):
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            ticker = Ticker(symbol + '.T')
            df = ticker.all_financial_data()
            df = df.reset_index().set_index(['symbol', 'asOfDate'])

            print(f"{symbol}の財務データ取得しました。")
            return df

        except (ChunkedEncodingError, ProtocolError):
            if attempt == max_retries - 1:
                logger.error(f"{symbol} の財務データ取得で接続エラー（最終試行失敗）:\n%s", traceback.format_exc())
                raise
            print(f"接続エラーが発生しました。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)

        except Exception:
            logger.error(f"{symbol} の財務データ取得中にエラー:\n%s", traceback.format_exc())
            return pd.DataFrame()

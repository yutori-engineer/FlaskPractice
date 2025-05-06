import logging
import pandas as pd
import time
from datetime import date
from yahooquery import Ticker
from requests.exceptions import ChunkedEncodingError
from urllib3.exceptions import ProtocolError
import traceback
from logger_config import setup_logger

# --- ログ設定 ---
logger = setup_logger('stock_logger', level=logging.INFO)


# --- 共通関数: リトライ付きデータ取得 ---
def fetch_with_retry(func, symbol, max_retries=5, retry_delay=5, label="データ"):
    for attempt in range(max_retries):
        try:
            return func(symbol)
        except (ChunkedEncodingError, ProtocolError) as e:
            logger.warning(f"{symbol} の{label}取得で接続エラー: {str(e)} (試行 {attempt + 1}/{max_retries})")
        except Exception as e:
            logger.error(f"{symbol} の{label}取得中にエラー:\n{traceback.format_exc()}")
            return pd.DataFrame()  # 汎用エラーでは空DataFrameを返す
        time.sleep(retry_delay * (2 ** attempt))  # 指数バックオフ
    logger.error(f"{symbol} の{label}取得に失敗しました（全{max_retries}回の試行後）")
    return pd.DataFrame()


# --- 共通関数: Ticker オブジェクト作成 ---
def get_ticker(symbol):
    if symbol[0].isdigit():
        return Ticker(symbol + '.T')  # 証券コード（数値）の場合、.T を付加
    else:
        return Ticker(symbol)         # ティッカー（アルファベット）の場合はそのまま


# --- 株価履歴データ取得 ---
def get_stock_history(symbol, period='1y', interval='1d'):
    def task(sym):
        ticker = get_ticker(sym)
        df = ticker.history(period=period, interval=interval)

        if df.empty or 'close' not in df.columns:
            logger.warning(f"{sym} の株価データが取得できませんでした。")
            return pd.DataFrame()

        df["MA5"] = df["close"].rolling(window=5).mean()
        df["MA20"] = df["close"].rolling(window=20).mean()
        df["MA60"] = df["close"].rolling(window=60).mean()

        logger.info(f"{sym} の株価時系列（{interval}）を取得しました。")
        return df

    return fetch_with_retry(task, symbol, label="株価時系列")


# --- 株価KPIデータ取得 ---
def get_financial_data(symbol):
    def task(sym):
        ticker = get_ticker(sym)
        financial_data = ticker.financial_data

        keys = list(financial_data.keys())
        if not keys:
            logger.warning(f"{sym} のKPIデータが存在しません。")
            return pd.DataFrame()

        first_symbol = keys[0]
        data = financial_data[first_symbol]
        df = pd.DataFrame([data])
        df["symbol"] = first_symbol
        df["date"] = date.today().strftime('%Y-%m-%d')
        df = df.set_index(['symbol', 'date'])

        logger.info(f"{sym} の株価KPIデータを取得しました。")
        return df

    return fetch_with_retry(task, symbol, label="KPIデータ")


# --- 財務データ取得 ---
def get_all_financial_data(symbol):
    def task(sym):
        ticker = get_ticker(sym)

        try:
            df = ticker.all_financial_data()
        except AttributeError:
            logger.error(f"{sym} の all_financial_data() はサポートされていないか利用不可です。")
            return pd.DataFrame()

        if df.empty:
            logger.warning(f"{sym} の財務データが取得できませんでした。")
            return pd.DataFrame()

        df = df.reset_index().set_index(['symbol', 'asOfDate'])
        logger.info(f"{sym} の財務データを取得しました。")
        return df

    return fetch_with_retry(task, symbol, label="財務データ")


# --- 実行例 ---
if __name__ == '__main__':
    symbol = '6758'
    print(get_financial_data(symbol))
    print(get_all_financial_data(symbol))
    print(get_stock_history(symbol))

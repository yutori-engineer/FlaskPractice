from yahooquery import Ticker
import pandas as pd
from datetime import date

def get_stock_history(symbol, period='1y', interval='1d'):
    try:
        ticker = Ticker(symbol + '.T')
        df = ticker.history(period=period, interval=interval)

        # --- 移動平均線の計算 ---
        df["MA5"] = df["close"].rolling(window=5).mean()
        df["MA20"] = df["close"].rolling(window=20).mean()
        df["MA60"] = df["close"].rolling(window=60).mean()
        
        return df
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None 
    
def get_financial_data(symbol):
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
        
        return df
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

def get_all_financial_data(symbol):
    try:
        ticker = Ticker(symbol + '.T')
        df = ticker.all_financial_data()
        df = df.reset_index()
        df = df.set_index(['symbol', 'asOfDate'])  
    
        return df
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None
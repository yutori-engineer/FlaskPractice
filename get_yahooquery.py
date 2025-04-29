from yahooquery import Ticker
import pandas as pd

def get_stock_data(symbol, period='1y', interval='1d'):
    try:
        ticker = Ticker(symbol + '.T')
        df = ticker.history(period=period, interval=interval)
        # インデックスをリセットしてdate列を作成(元データはsymbolとdateの複合インデックス)
        df = df.reset_index()
        
        # date列の名前を確認して変更
        if 'date' not in df.columns:
            df = df.rename(columns={df.columns[0]: 'date'})
            
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
        
        # 必要な列を選択
        columns = [
            'currentPrice', 'targetHighPrice', 'targetLowPrice', 'targetMeanPrice',
            'targetMedianPrice', 'recommendationMean', 'recommendationKey',
            'numberOfAnalystOpinions', 'totalCash', 'totalDebt', 'totalRevenue',
            'revenueGrowth', 'grossProfits', 'freeCashflow', 'operatingCashflow',
            'earningsGrowth', 'revenueGrowth', 'grossMargins', 'ebitdaMargins',
            'operatingMargins', 'profitMargins', 'returnOnAssets', 'returnOnEquity'
        ]
        
        # 存在する列のみを選択
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]
        
        return df
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None
    
        return df

def get_all_financial_data(symbol):
    try:
        ticker = Ticker(symbol + '.T')
        all_financial_data = ticker.all_financial_data()
    
        return all_financial_data
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None
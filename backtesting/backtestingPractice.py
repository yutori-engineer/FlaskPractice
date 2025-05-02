import sqlite3
import pandas as pd
from backtesting import Backtest
import stock_list as sl
import get_stock as gs
import backtesting.strategies as st

# 結果配列の準備
result = []
bt = []

#銘柄リストを取得
stock_list = sl.stock_list

# データリストからデータを取得しDB書き込み
for i in range(len(stock_list)):
    stock_name = stock_list[i][0]
    symbol = gs.get_stock_data(stock_name)
    print(symbol)
    
 # DBからデータ読み込み、バックテスト実施   
for code in stock_list:
    conn = sqlite3.connect('stock_data.db')
    query = f"SELECT Date,Open,Close,High,Low,Volume FROM historical_price WHERE Symbol = '{code[0]}.T'"
    data = pd.read_sql_query(query, conn)
    
    # データが空でないか確認
    print(f"Symbol: {code[0]}.T")
    print(f"Data shape before cleaning: {data.shape}")
    
    # 日付カラムをDateTimeIndexに変換
    data['Date'] = pd.to_datetime(data['Date'])
    # data['Date'] = data['Date'].dt.tz_convert('Asia/Tokyo') #日本時間へ変換（不要）
    data.set_index('Date', inplace=True)
    
    # 欠損値を含む行を削除
    data = data.dropna()
    print(f"Data shape after cleaning: {data.shape}")
    
    # データが空の場合はスキップ
    if data.empty:
        print(f"Skipping {code[0]} due to empty data")
        conn.close()
        continue

    conn.close()

    # Backtestを使用して戦略を実行
    bt = Backtest(data, st.BreakOut, cash=1000000, commission=.000,
                  exclusive_orders=True)
    stats = bt.run()
    
    # statsをDataFrameに変換し、Timestamp型を文字列に変換する前に
    conn = sqlite3.connect('stock_data.db', timeout=10)
    
    # テーブルが存在しない場合は新規作成（これによりカラムも自動的に作成される）
    stats_df = pd.DataFrame([stats]).reset_index()
    stats_df = stats_df.astype(str)  # すべての列を文字列型に変換
    stats_df['symbol'] = code
    stats_df = stats_df.set_index('symbol')
    
    # replace='replace'を使用して最初の実行時にテーブルを作成
    stats_df.to_sql('stat_results', conn, if_exists='append' if code == stock_list[0] else 'append', index=True)
    conn.close()

    bt.plot()
    print(code)
    # print(stats_df)
    # print(type(stats_df))
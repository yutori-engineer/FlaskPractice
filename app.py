import os
from flask import Flask, render_template, request
from yahooquery import Ticker
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    table_html = ''  # テーブルのHTMLを初期化
    chart_html = ''  # チャートのHTMLを初期化
    symbol = ''      # symbolを初期化
    
    if request.method == 'POST':
        symbol = request.form['symbol']
        data = get_stock_data(symbol)
        chart_html = create_candlestick_with_volume(data, symbol)       
        if data is not None:            # データを日付でソートし、順序を逆にする
            data = data.sort_index(ascending=False)
            table_html = data.to_html(classes='table table-striped table-hover table-sm', index=True)
            return render_template('index.html', plot=True, table_html=table_html, chart_html=chart_html, symbol=symbol)
    return render_template('index.html', plot=False, table_html=table_html, chart_html=chart_html, symbol=symbol)

def get_stock_data(symbol):
    try:
        ticker = Ticker(symbol + '.T')
        df = ticker.history(period='1y',interval='1d')
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

def create_candlestick_with_volume(df, symbol):

    fig = go.Figure()

    # --- ローソク足 ---
    fig.add_trace(go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="株価",
        yaxis="y1"
    ))

    # 移動平均線（5日）
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["MA5"],
        mode="lines",
        line=dict(color="blue", width=1.5),
        name="5日移動平均"
    ))

    # 移動平均線（20日）
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["MA20"],
        mode="lines",
        line=dict(color="red", width=1.5),
        name="20日移動平均"
    ))
    
        # 移動平均線（60日）
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df["MA60"],
        mode="lines",
        line=dict(color="green", width=1.5),
        name="60日移動平均"
    ))
    # --- 出来高（棒グラフ） ---
    fig.add_trace(go.Bar(
        x=df["date"],
        y=df["volume"],
        name="出来高",
        marker_color="lightblue",
        yaxis="y2"
    ))

    # --- レイアウト調整（2段に分ける） ---
    fig.update_layout(
        title=f"{symbol} 日足ローソクチャート + 出来高",
        xaxis=dict(domain=[0, 1], rangeslider_visible=False),
        yaxis=dict(title="株価", domain=[0.3, 1]),      # 上：ローソク足
        yaxis2=dict(title="出来高", domain=[0, 0.25]),   # 下：出来高バー
        height=700,
        template="plotly_white",
        showlegend=False
    )

    return pio.to_html(fig, full_html=False)

if __name__ == '__main__':
    app.run(debug=True)
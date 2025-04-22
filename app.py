import os
from flask import Flask, render_template, request
from yahooquery import Ticker
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import japanize_matplotlib 
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
        plot_png(data, symbol)
        # chart_html = create_candlestick_chart(data, symbol) 
        chart_html = create_candlestick_with_volume(data, symbol)       
        if data is not None:            # データを日付でソートし、順序を逆にする
            data = data.sort_index(ascending=False)
            table_html = data.to_html(classes='table table-striped table-hover table-sm', index=True)
            return render_template('index.html', plot=True, table_html=table_html, chart_html=chart_html, symbol=symbol)
    return render_template('index.html', plot=False, table_html=table_html, chart_html=chart_html, symbol=symbol)

def get_stock_data(symbol):
    try:
        ticker = Ticker(symbol + '.T')
        df = ticker.history(period='1y',interval='1d') #(period='1y', interval='1d')
        return df
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

def plot_png(data, symbol):
    # キャンドルスティックチャートのためにデータを整形
    data.reset_index(inplace=True)
    data.set_index('date', inplace=True)
    data.index = pd.to_datetime(data.index)

    # プロット画像を static フォルダに保存
    plot_path = os.path.join('static', 'plot.png')
    
    # フィギュアサイズを大きくする
    fig_size = (30, 10)  # 幅20インチ、高さ10インチ
    
    # # スタイル設定
    # mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
    # s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False, rc={"font.family":'IPAexGothic'})
    s  = mpf.make_mpf_style(base_mpf_style='yahoo', rc={"font.family":'IPAexGothic'})

    # プロット
    mpf.plot(data, type='candle', style=s, title=f'{symbol} -日足チャート',
             ylabel='Price', volume=True, figsize=fig_size, show_nontrading=True,
             tight_layout = True, mav=(5,20,60),
             savefig=dict(fname=plot_path, dpi=100, bbox_inches='tight'))
    
def create_candlestick_chart(df, symbol):
    # print("データフレームの列:", df.columns)  # 利用可能な列名を確認
    df = df.reset_index()
    # print("リセット後の列:", df.columns)  # リセット後の列名を確認
    fig = go.Figure(data=[
        go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol
        )
    ])
    fig.update_layout(
        title=f"{symbol} 日足ローソクチャート",
        xaxis_title="日付",
        yaxis_title="株価（円）",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=600
    )

    # HTML文字列としてチャートを返す
    return pio.to_html(fig, full_html=False)

def create_candlestick_with_volume(df, symbol):
    # インデックスをリセットしてdate列を作成
    df = df.reset_index()
    
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
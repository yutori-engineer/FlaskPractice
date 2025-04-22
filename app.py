import os
from flask import Flask, render_template, request
from yahooquery import Ticker
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import japanize_matplotlib 


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    table_html = ""  # 初期値を設定
    if request.method == 'POST':
        symbol = request.form['symbol']
        data = get_stock_data(symbol)
        plot_png(data, symbol)        
        if data is not None:            # データを日付でソートし、順序を逆にする
            data = data.sort_index(ascending=False)
            table_html = data.to_html(classes='table table-striped table-hover table-sm', index=True)
            return render_template('index.html', plot=True, table_html=table_html)
    return render_template('index.html', plot=False, table_html=table_html)

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

if __name__ == '__main__':
    app.run(debug=True)
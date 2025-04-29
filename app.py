import os
from flask import Flask, render_template, request
import pandas as pd
from get_yahooquery import get_stock_data, get_financial_data, get_all_financial_data
from create_chart import create_candlestick_with_volume

app = Flask(__name__)

# 列名の日本語翻訳辞書
COLUMN_TRANSLATIONS = {
    'currentPrice': '現在の株価',
    'targetHighPrice': '目標高値',
    'targetLowPrice': '目標安値',
    'targetMeanPrice': '目標平均価格',
    'targetMedianPrice': '目標中央価格',
    'recommendationMean': '推奨平均',
    'recommendationKey': '推奨',
    'numberOfAnalystOpinions': 'アナリスト意見数',
    'totalCash': '現金総額',
    'totalDebt': '負債総額',
    'totalRevenue': '総収益',
    'revenueGrowth': '収益成長率',
    'grossProfits': '粗利益',
    'freeCashflow': 'フリーキャッシュフロー',
    'operatingCashflow': '営業キャッシュフロー',
    'earningsGrowth': '利益成長率',
    'grossMargins': '粗利益率',
    'ebitdaMargins': 'EBITDAマージン',
    'operatingMargins': '営業利益率',
    'profitMargins': '純利益率',
    'returnOnAssets': '総資産利益率',
    'returnOnEquity': '自己資本利益率'
}

@app.route('/', methods=['GET', 'POST'])
def index():
    table_html = ''  # テーブルのHTMLを初期化
    chart_html = ''  # チャートのHTMLを初期化
    symbol = ''      # symbolを初期化
    financial_html = ''  # 財務データのHTMLを初期化
    financial_data_raw_html = ''  # 生の財務データのHTMLを初期化
    
    if request.method == 'POST':
        symbol = request.form['symbol']
        data = get_stock_data(symbol, period='1y', interval='1d')
        financial_data = get_financial_data(symbol)
        all_financial_data = get_all_financial_data(symbol)
        
        # 目標株価のデータを準備
        target_prices = {}
        if financial_data is not None:
            target_prices = {
                'targetHighPrice': financial_data['targetHighPrice'].iloc[0] if 'targetHighPrice' in financial_data.columns else None,
                'targetLowPrice': financial_data['targetLowPrice'].iloc[0] if 'targetLowPrice' in financial_data.columns else None,
                'targetMeanPrice': financial_data['targetMeanPrice'].iloc[0] if 'targetMeanPrice' in financial_data.columns else None,
                'targetMedianPrice': financial_data['targetMedianPrice'].iloc[0] if 'targetMedianPrice' in financial_data.columns else None
            }
        
        chart_html = create_candlestick_with_volume(data, symbol, target_prices)       
        
        if data is not None:
            # データを日付でソートし、順序を逆にする
            data = data.sort_index(ascending=False)
            table_html = data.to_html(classes='table table-striped table-hover table-sm', index=True)
            
            # 財務データをHTMLテーブルに変換
            if financial_data is not None:
                # 生の財務データをHTMLに変換
                financial_data_raw_html = all_financial_data.to_html(classes='table table-striped table-hover table-sm')
                
                # 列名を日本語に変換
                financial_data = financial_data.rename(columns=COLUMN_TRANSLATIONS)
                
                # 数値のフォーマットを設定
                for col in financial_data.columns:
                    if pd.api.types.is_numeric_dtype(financial_data[col]):
                        financial_data[col] = financial_data[col].apply(
                            lambda x: f'{x:,.2f}' if pd.notnull(x) else 'N/A'
                        )
                
                # 列を3つのグループに分ける
                columns = list(financial_data.columns)
                group_size = (len(columns) + 2) // 3  # 3つのグループに均等に分割
                
                financial_html = ''
                for i in range(0, len(columns), group_size):
                    group_columns = columns[i:i + group_size]
                    group_data = financial_data[group_columns]
                    financial_html += group_data.to_html(
                        classes='table table-striped table-hover table-sm',
                        index=False
                    )
                    financial_html += '<div class="mb-4"></div>'  # グループ間に余白を追加
            
            return render_template('index.html', 
                                 plot=True, 
                                 table_html=table_html, 
                                 chart_html=chart_html, 
                                 financial_html=financial_html,
                                 financial_data_raw_html=financial_data_raw_html,
                                 symbol=symbol)
    
    return render_template('index.html', 
                         plot=False, 
                         table_html=table_html, 
                         chart_html=chart_html, 
                         financial_html=financial_html,
                         financial_data_raw_html=financial_data_raw_html,
                         symbol=symbol)

if __name__ == '__main__':
    app.run(debug=True)
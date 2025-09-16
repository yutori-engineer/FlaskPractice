import os
from flask import Flask, render_template, request
import pandas as pd
from get_yahooquery import get_stock_history, get_financial_data, get_all_financial_data
from create_chart import create_candlestick,create_lineChart
from static.translations import COLUMN_TRANSLATIONS
from sqlite_rw  import read_sqlite

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    table_html = ''  # テーブルのHTMLを初期化
    chart_html = ''  # チャートのHTMLを初期化
    chart_html2 = ''  # チャートのHTMLを初期化
    chart_html3 = ''  # チャートのHTMLを初期化
    linechart_html3 = ''  # チャートのHTMLを初期化
    symbol = ''      # symbolを初期化
    financial_html = ''  # 財務データのHTMLを初期化
    financial_data_raw_html = ''  # 生の財務データのHTMLを初期化
    show_raw_data = False  # デフォルトで非表示

    # チャート用の前処理（空や列欠損を弾き、date列を正規化）
    def prepare_for_chart(df: pd.DataFrame):
        if df is None or df.empty:
            return None
        cols_lower = {c.lower() for c in df.columns}
        need = {'open', 'high', 'low', 'close'}
        if not need.issubset(cols_lower):
            return None
        if 'date' not in df.columns:
            for c in ['Datetime', 'datetime', 'Date', 'time', 'Time']:
                if c in df.columns:
                    df = df.rename(columns={c: 'date'})
                    break
        if 'date' not in df.columns:
            # indexに日時が入っているケースに対応
            if df.index.name and df.index.name.lower() in ['date', 'datetime']:
                df = df.reset_index().rename(columns={df.index.name: 'date'})
            else:
                return None
        return df
    
    if request.method == 'POST':
        symbol = request.form['symbol']
        show_raw_data = request.form.get('show_raw_data', 'false') == 'true'  # チェックボックスの状態を取得
        history_data = pd.DataFrame()
        history_data2 = pd.DataFrame()
        history_data3 = pd.DataFrame()
        financial_data = pd.DataFrame()
        all_financial_data = pd.DataFrame()
        db_path = ".\\stock_data.db"
        
        # try:
        #     table_name = 'stock_history_1d'
        #     history_data = read_sqlite(db_path, table_name, symbol)
        #     if history_data.empty:
        #         raise ValueError("Empty DataFrame")  # 強制的にexceptに飛ばす
        # except Exception:
        try:
            history_data = get_stock_history(symbol, period='1y', interval='1d').reset_index()
        except Exception:
            history_data = pd.DataFrame()
            
        # try:
        #     table_name = 'stock_history_5m'
        #     history_data2 = read_sqlite(db_path, table_name, symbol).reset_index()
        #     if history_data2.empty:
        #         raise ValueError("Empty DataFrame")  # 強制的にexceptに飛ばす
        # except Exception:           
        try:
            history_data2 = get_stock_history(symbol, period='60d', interval='5m').reset_index()
        except Exception:
            history_data2 = pd.DataFrame()

        # try:
        #     table_name = 'stock_history_1mo'
        #     history_data3 = read_sqlite(db_path, table_name, symbol).reset_index()
        #     if history_data3.empty:
        #         raise ValueError("Empty DataFrame")  # 強制的にexceptに飛ばす
        # except Exception:         
        try:
            history_data3 = get_stock_history(symbol, period='max', interval='1mo').reset_index()
        except Exception:
            history_data3 = pd.DataFrame()
            
        # try:
        #     table_name = 'financial_data'
        #     financial_data = read_sqlite(db_path, table_name, symbol).reset_index()
        #     if financial_data.empty:
        #         raise ValueError("Empty DataFrame")  # 強制的にexceptに飛ばす
        # except Exception:               
        try:
            financial_data = get_financial_data(symbol).reset_index()
        except Exception:
            financial_data = pd.DataFrame()
            
        # try:
        #     table_name = 'all_financial_data'
        #     all_financial_data = read_sqlite(db_path, table_name, symbol).reset_index()
        #     if all_financial_data.empty:
        #         raise ValueError("Empty DataFrame")  # 強制的にexceptに飛ばす
        # except Exception:                 
        try:
            all_financial_data = get_all_financial_data(symbol).reset_index()
        except Exception:
            all_financial_data = pd.DataFrame()
        
        # 目標株価のデータを準備
        target_prices = {}
        if financial_data is not None and not financial_data.empty:
            target_prices = {
                'targetHighPrice': financial_data['targetHighPrice'].iloc[0] if 'targetHighPrice' in financial_data.columns else None,
                'targetLowPrice': financial_data['targetLowPrice'].iloc[0] if 'targetLowPrice' in financial_data.columns else None,
                'targetMeanPrice': financial_data['targetMeanPrice'].iloc[0] if 'targetMeanPrice' in financial_data.columns else None,
                'targetMedianPrice': financial_data['targetMedianPrice'].iloc[0] if 'targetMedianPrice' in financial_data.columns else None
            }
        
        # チャート生成前に安全化
        chart1_df = prepare_for_chart(history_data)
        chart2_df = prepare_for_chart(history_data2)
        chart3_df = prepare_for_chart(history_data3)

        chart_html = create_candlestick(chart1_df, symbol, target_prices) if chart1_df is not None else ''
        chart_html2 = create_candlestick(chart2_df, symbol, target_prices) if chart2_df is not None else ''
        chart_html3 = create_candlestick(chart3_df, symbol, target_prices) if chart3_df is not None else ''
        linechart_html3 = create_lineChart(chart3_df, symbol) if chart3_df is not None else ''
        
        if history_data is not None and not history_data.empty:
            # データを日付でソートし、順序を逆にする
            history_data = history_data.sort_index(ascending=False)
            table_html = history_data.to_html(classes='table table-striped table-hover table-sm', index=True)
        if all_financial_data is not None and not all_financial_data.empty:
            all_financial_data = all_financial_data.sort_values('asOfDate', ascending=False)
            
        # 財務データをHTMLテーブルに変換
        if financial_data is not None and not financial_data.empty:
            # 列名を日本語に変換
            financial_data = financial_data.rename(columns=COLUMN_TRANSLATIONS)         
            if all_financial_data is not None and not all_financial_data.empty:
                all_financial_data = all_financial_data.rename(columns=COLUMN_TRANSLATIONS)

            # 生の財務データをHTMLに変換
            if all_financial_data is not None and not all_financial_data.empty:
                financial_data_raw_html = all_financial_data.to_html(classes='table table-striped table-hover table-sm')
            
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
            
        any_plot = any([chart_html, chart_html2, chart_html3, linechart_html3, table_html, financial_html, financial_data_raw_html])
        return render_template('index.html', 
                             plot=any_plot, 
                             table_html=table_html, 
                             chart_html=chart_html, 
                             chart_html2=chart_html2, 
                             chart_html3=chart_html3,
                             linechart_html3=linechart_html3,
                             financial_html=financial_html,
                             financial_data_raw_html=financial_data_raw_html,
                             show_raw_data=show_raw_data,
                             symbol=symbol)
    
    return render_template('index.html', 
                         plot=False, 
                         table_html=table_html, 
                         chart_html=chart_html, 
                         chart_html2=chart_html2,
                         chart_html3=chart_html3,
                         linechart_html3=linechart_html3,
                         financial_html=financial_html,
                         financial_data_raw_html=financial_data_raw_html,
                         show_raw_data=show_raw_data,
                         symbol=symbol)

if __name__ == '__main__':
    app.run(debug=True)
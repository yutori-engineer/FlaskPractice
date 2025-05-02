import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_candlestick(data, symbol, target_prices=None):
    print(data.columns)
    print(data.head())
    print(data.dtypes)  # これで date の型を確認
    
    # サブプロットを作成
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.03, 
                       row_heights=[0.7, 0.3])
    
    # ローソク足チャートを追加
    fig.add_trace(
        go.Candlestick(
            x=data['date'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='価格'
        ),
        row=1, col=1
    )
    
    # 移動平均線を追加
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['MA5'],
            name='5日移動平均',
            line=dict(color='black', width=1),
            visible=False
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['MA20'],
            name='20日移動平均',
            line=dict(color='black', width=1),
            visible=False
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['MA60'],
            name='60日移動平均',
            line=dict(color='black', width=1),
            visible=False
        ),
        row=1, col=1
    )
    
    # 目標価格の水平線を追加
    if target_prices:
        colors = {
            'targetHighPrice': 'black',
            'targetLowPrice': 'black',
            'targetMeanPrice': 'red',
            'targetMedianPrice': 'black'
        }
        
        labels = {
            'targetHighPrice': '目標高値',
            'targetLowPrice': '目標安値',
            'targetMeanPrice': '目標平均価格',
            'targetMedianPrice': '目標中央価格'
        }
        
        for key, price in target_prices.items():
            if price is not None:
                # 水平線を追加
                fig.add_shape(
                    type="line",
                    x0=data['date'].iloc[0],
                    y0=price,
                    x1=data['date'].iloc[-1],
                    y1=price,
                    line=dict(
                        color=colors[key],
                        width=1.5,
                        dash="dash",
                    ),
                    name=labels[key],
                    row=1, col=1
                )
                
                # ラベルと値を表示
                fig.add_annotation(
                    x=data['date'].iloc[1],
                    y=price,
                    text=f"{labels[key]}: {price:,.2f}",
                    showarrow=False,
                    yshift=10,
                    xref="x",
                    yref="y",
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(
                        size=12,
                        color=colors[key]
                    ),
                    row=1, col=1
                )
    
    # 出来高チャートを追加
    fig.add_trace(
        go.Bar(
            x=data['date'],
            y=data['volume'],
            name='出来高',
            marker_color='blue'
            ,marker_line=dict(width=1, color='black')  # 線の太さと色
        ),
        row=2, col=1
    )
    
    # レイアウトを設定
    fig.update_layout(
        title=f'{symbol} 株価チャート',
        yaxis_title='株価',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True
    )
    
    # X軸の設定
    fig.update_xaxes(
        rangeslider_visible=False,
        row=1, col=1,
        tickformat="%Y-%m-%d",
        tickangle=45
    )
    
    # Y軸の設定
    fig.update_yaxes(
        title_text="株価", 
        row=1, col=1,
        title_standoff=0,
        side="right"
    )
    fig.update_yaxes(
        title_text="出来高", 
        row=2, col=1,
        title_standoff=0,
        side="right"
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def create_lineChart(data, symbol):
    # サブプロットを作成
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.03, 
                       row_heights=[0.7, 0.3])
    
    #修正終値の線チャートを追加
    fig.add_trace(
        go.Scatter(
        x=data['date'],
        y=data['adjclose'],
        name='修正終値',
        line=dict(color='red', width=2),
        visible=True
    ),
        row=1, col=1
    )
 
    # 出来高チャートを追加
    fig.add_trace(
        go.Bar(
            x=data['date'],
            y=data['volume'],
            name='出来高',
            marker_color='blue'
            ,marker_line=dict(width=1, color='black')  # 線の太さと色
        ),
        row=2, col=1
    )
    
    # レイアウトを設定
    fig.update_layout(
        title=f'{symbol} 株価チャート',
        yaxis_title='株価',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True
    )
    
    # X軸の設定
    fig.update_xaxes(
        rangeslider_visible=False,
        row=1, col=1,
        tickformat="%Y-%m-%d",
        tickangle=45
    )
    
    # Y軸の設定
    fig.update_yaxes(
        title_text="株価", 
        row=1, col=1,
        title_standoff=0,
        side="right"
    )
    fig.update_yaxes(
        title_text="出来高", 
        row=2, col=1,
        title_standoff=0,
        side="right"
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
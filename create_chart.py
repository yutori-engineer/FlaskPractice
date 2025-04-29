import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import plotly.io as pio

def create_candlestick_with_volume(data, symbol, target_prices=None):
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
                        width=2,
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
        ),
        row=2, col=1
    )
    
    # レイアウトを設定
    fig.update_layout(
        title=f'{symbol} 株価チャート',
        yaxis_title='価格',
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
        title_text="価格", 
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
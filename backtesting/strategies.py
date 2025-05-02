import pandas as pd
from backtesting import Strategy # バックテスト、ストラテジー
from backtesting.lib import crossover
from backtesting.lib import SignalStrategy, TrailingStrategy
from backtesting.lib import resample_apply,OHLCV_AGG
import talib as ta
import datetime

def SMA(array, n):
    """Simple moving average"""
    return pd.Series(array).rolling(n).mean()


def RSI(array, n):
    """Relative strength index"""
    # Approximate; good enough
    gain = pd.Series(array).diff()
    loss = gain.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    rs = gain.ewm(n).mean() / loss.abs().ewm(n).mean()
    return 100 - 100 / (1 + rs)

def MACD(close, n1, n2, ns):
    macd, macdsignal, macdhist = ta.MACD(close, fastperiod=n1, slowperiod=n2, signalperiod=ns)
    return macd, macdsignal

class MACDCross(Strategy):
    n1 = 12 #短期EMAの期間
    n2 = 26 #長期EMAの期間
    ns = 9 #シグナル（MACDのSMA）の期間

    def init(self):
        self.macd, self.macdsignal = self.I(MACD, self.data.Close, self.n1, self.n2, self.ns)

    def next(self): # チャートデータの行ごとに呼び出される
        if crossover(self.macd, self.macdsignal): #macdがsignalを上回った時
            self.buy() # 買い
        elif crossover(self.macdsignal, self.macd): #signalがmacdを上回った時
            self.position.close() # 売り

class SmaCross(SignalStrategy,
               TrailingStrategy):  #Library of Composable Base Strategies
    n1 = 1
    n2 = 20
    
    def init(self):
        # In init() and in next() it is important to call the
        # super method to properly initialize the parent classes
        super().init()
        
        # Precompute the two moving averages
        sma1 = self.I(SMA, self.data.Close, self.n1)
        sma2 = self.I(SMA, self.data.Close, self.n2)
        
        # Where sma1 crosses sma2 upwards. Diff gives us [-1,0, *1*]
        signal = (pd.Series(sma1) > sma2).astype(int).diff().fillna(0)
        signal = signal.replace(-1, 0)  # Upwards/long only
        
        # Use 95% of available liquidity (at the timde) on each order.
        # (Leaving a value of 1. would instead buy a single share.)
        entry_size = signal * .95
                
        # Set order entry sizes using the method provided by 
        # `SignalStrategy`. See the docs.
        self.set_signal(entry_size=entry_size)
        
        # Set trailing stop-loss to 2x ATR using
        # the method provided by `TrailingStrategy`
        self.set_trailing_sl(2)

class System(Strategy): # Multiple Time Frames
    d_rsi = 30  # Daily RSI lookback periods
    w_rsi = 30  # Weekly
    level = 70
    
    def init(self):
        # Compute moving averages the strategy demands
        self.ma10 = self.I(SMA, self.data.Close, 10)
        self.ma20 = self.I(SMA, self.data.Close, 20)
        self.ma50 = self.I(SMA, self.data.Close, 50)
        self.ma100 = self.I(SMA, self.data.Close, 100)
        
        # Compute daily RSI(30)
        self.daily_rsi = self.I(RSI, self.data.Close, self.d_rsi)
        
        # To construct weekly RSI, we can use `resample_apply()`
        # helper function from the library
        self.weekly_rsi = resample_apply(
            'W-FRI', RSI, self.data.Close, self.w_rsi)
        
        
    def next(self):
        price = self.data.Close[-1]
        
        # If we don't already have a position, and
        # if all conditions are satisfied, enter long.
        if (not self.position and
            self.daily_rsi[-1] > self.level and
            self.weekly_rsi[-1] > self.level and
            self.weekly_rsi[-1] > self.daily_rsi[-1] and
            self.ma10[-1] > self.ma20[-1] > self.ma50[-1] > self.ma100[-1] and
            price > self.ma10[-1]):
            
            # Buy at market price on next open, but do
            # set 8% fixed stop loss.
            self.buy(sl=.92 * price)
        
        # If the price closes 2% or more below 10-day MA
        # close the position, if any.
        elif price < .98 * self.ma10[-1]:
            self.position.close()
            
        # print(self.daily_rsi)
        # print(type(self.daily_rsi))
        # print(self.weekly_rsi)
        # print(type(self.weekly_rsi))         
        pass
class BreakOut(Strategy):
    # Define the two MA lags as *class variables*
    # for later optimization
    n1 = 20
    n2 = 66
    
    def init(self):
        # Precompute the two moving averages
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
        
        # self.dataをpandas DataFrameに変換してから日単位で集計処理する
        self.day_price = pd.DataFrame(self.data.df).resample('1D').agg(OHLCV_AGG).dropna()

    def next(self):
        #当日値を取得
        present_day = (self.data.index[-1]).replace(hour=0, minute=0, second=0, microsecond=0)
        # 現在の時刻を取得
        current_time = self.data.index[-1].time()
        # 比較用の時刻オブジェクトを作成
        start = datetime.time(9, 10)
        end = datetime.time(11, 10)

        try:
            target_index = self.day_price.index.get_loc(present_day)
            if target_index > 0:
                previous_row = self.day_price.iloc[target_index - 1]
                # print(previous_row)
                # print(self.data)
                
                # 時間の範囲をチェック
                if start <= current_time <= end:
                    # print('ClosePrice'+str(self.data.Close[-1]))
                    # print('PreviousHigh'+str(previous_row.High))
                    if self.data.Close[-1] > previous_row.High and self.data.Close[-1] < previous_row.High * 1.04 and self.position.size == 0:
                         self.buy() # size=100
                        #  print('###BuyBuy###')
                         
            else:
                pass
                # print("前日足は存在しません。")
        except KeyError:
            print(f"指定した日付が見つかりません: {present_day}")
        
        # if len(self.trades) > 0:  # トレードが存在する場合のみ
            # print('EntryBar'+str(self.trades[-1].entry_bar))
            # print('EntryTime'+str(self.trades[-1].entry_time))
            # print('EntryPrice'+str(self.trades[-1].entry_price))
        
        # print('CurrentTime: ' + str(current_time))
        # print('EndTime: ' + str(end))
        # print('PositionSize: ' + str(self.position.size))        
        
        if self.position and current_time > end:
            self.position.close()
            # print('###CloseClose###')
            
        pass

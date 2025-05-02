import pandas_datareader.data as pdr
import matplotlib.pyplot as plt
from prophet import Prophet

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#まずは取得した株価のをデータフレームを日付けのインデックスで昇順にソートするメソッドを作成する。
def get_stock_data(code):
  df = pdr.DataReader("{}.jp".format(code),"stooq").sort_index()
  return df


df = get_stock_data("8053")
# print(df)

df['ds'] = df.index
df = df.rename({'Close':'y'}, axis=1)

# 不要カラムの削除と並べ替え
df = df[['ds', 'y']]

# 学習データとテストデータの分割
df_train = df.loc[:'2024-01-01']
df_test = df.loc['2024-01-01':]

# print(df_train)
# print(df_train.isna().sum())  # NaN値の数を確認する


params = {'growth': 'linear',
          'changepoints': None,
          'n_changepoints': 25,
          'changepoint_range': 0.8,
          'yearly_seasonality': 'auto',
          'weekly_seasonality': 'auto',
          'daily_seasonality': 'auto',
          'holidays': None,
          'seasonality_mode': 'additive',
          'seasonality_prior_scale': 10.0,
          'holidays_prior_scale': 10.0,
          'changepoint_prior_scale': 0.05,
          'mcmc_samples': 0,
          'interval_width': 0.80,
          'uncertainty_samples': 1000,
          'stan_backend': None
         }

# Prophet 予測モデル構築
df_prophet_model = Prophet(**params)
df_prophet_model.fit(df_train)

# Prophet 予測モデルの精度検証用データの生成
df_future = df_prophet_model.make_future_dataframe(periods=len(df_test), freq='d')
df_pred = df_prophet_model.predict(df_future)

# Prophet 予測モデルの予測結果（学習データ期間＋テストデータ期間）
df_pred_plot = df_prophet_model.plot(df_pred)         #予測値（黒い点は学習データの実測値）
df_pmpc = df_prophet_model.plot_components(df_pred)   #モデルの要素分解（トレンド、週周期、年周期）

# テストデータに予測値を結合
df_test.loc[:, 'Prophet Predict'] = df_pred['yhat'].tail(len(df_test)).to_list()

plt.figure(figsize=[10, 7])

# 実測データと予測データの折れ線グラフを描画
df_test['y'].plot(title='Forecast evaluation', kind='line')
df_test['Prophet Predict'].plot(title='Forecast evaluation', kind='line')

# グラフの凡例を設定
plt.legend(['y', 'Prophet Predict'])

# x軸の範囲を変更する
plt.xlim('2024-01-01', '2024-09-30')
# y軸の範囲を変更する
plt.ylim(1500, 4000)

# グラフの表示
plt.show()



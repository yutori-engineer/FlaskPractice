import pandas_datareader.data as pdr
import mplfinance as mpf
from prophet import Prophet
import matplotlib
matplotlib.use('TkAgg')  # または 'Qt5Agg'
import matplotlib.pyplot as plt

# ... 残りのコード ...

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def get_stock_data(code):
  df = pdr.DataReader("{}.jp".format(code),"stooq").sort_index()
  return df

df = get_stock_data(4385)
df["ds"] = df.index
df = df.rename(columns={"Close": "y"})

#今後の株価を予測する
   
m = Prophet()
m.fit(df)
future = m.make_future_dataframe(periods=365)
forecast = m.predict(future)
plt = m.plot(forecast)
# plt = m.plot_components(forecast)
import matplotlib.pyplot as plt

plt.show()
plt.ion()


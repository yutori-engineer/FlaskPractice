#モジュールインポート
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader.data as pdr
import tensorflow as tf
from tensorflow import keras
from keras import layers
from sklearn.preprocessing import StandardScaler
plt.style.use('ggplot')

#window_sizeに分けて時系列データのデータセットを作成
def apply_window(data, window_size):
#データをwindow_sizeごとに分割
    sequence_length = window_size
    window_data = []
    for index in range(len(data) - window_size):
        window = data[index: index + sequence_length]
    window_data.append(window)
    return np.array(window_data)

#訓練データと検証データに分ける
def split_train_test(data, train_rate=0.7):
#データの古い方7割（デフォルト値0.7）を訓練用データとし、残りをテスト用データとする
    row = round(train_rate * data.shape[0])
    train = data[:row]
    test = data[row:]
    return train, test

def data_load():
#アサヒグループホールディングスの株価ファイル読み込み
    df= pdr.DataReader("2502.JP","stooq")
    df.reset_index(inplace= True)

    #Data列を日付データとして認識
    df['Date'] = pd.to_datetime(df['Date'])
    #日付順に並び替え
    df.sort_values(by='Date', inplace=True)
    #終値を抽出
    close_ts = df['Close']
    close_ts = np.expand_dims(close_ts, 1)
    return close_ts

def train_model(X_train, y_train, units=15):
#入力データの形式を取得
    input_size = X_train.shape[1:]

    #レイヤーを定義
    model = keras.Sequential()
    model.add(layers.LSTM(
        input_shape=input_size,
        units=units,
        dropout = 0.1,
        return_sequences=False,))
    model.add(layers.Dense(units=1))

    model.compile(loss='mse', optimizer='adam', metrics=['mean_squared_error'])
    def train_model(X_train, y_train, units=10):
    # ... 既存のコード ...
        model.fit(X_train, y_train,
              epochs=100,
              batch_size=32,
              verbose=1)
    
    # ... 既存のコード ...
    # model.fit(X_train, y_train,
    #                 epochs=10, validation_split=0.3, verbose=2, shuffle=False)
    return model

def predict(data, model):
    pred = model.predict(data,verbose=0)
    return pred.flatten()

#モデルに入力するデータ長
window_size = 15

#アサヒグループホールディングスの株価・終値を取得
close_ts = data_load()
# print(len(close_ts))

# データを訓練用・学習用に分割
train, test = split_train_test(close_ts)
# print(len(train))
# print(len(test))

#データを正規化
scaler = StandardScaler()
train = scaler.fit_transform(train)
test = scaler.transform(test)

#一定の長さのデータを作る
train = apply_window(train, window_size+1)
test = apply_window(test, window_size+1)
print(len(train))
print(len(test))

# #訓練用の入力データ
# X_train = train[:, :-1]
# # 訓練用の正解ラベル
# y_train = train[:,  -1]

# #テスト用の入力データ
# X_test = test[:, :-1]
# #テスト用の正解ラベル
# y_test = test[:,  -1]

# #学習モデルを取得
# model = train_model(X_train, y_train, units=15)

# #検証データで予測
# predicted = predict(X_test, model)
# predicted = predicted.reshape([-1, predicted.shape[0]])

# plt.figure(figsize=(15, 8))
# plt.plot(scaler.inverse_transform(y_test),label='True Data')
# plt.plot(scaler.inverse_transform(predicted).reshape([predicted.shape[1]]),label='Prediction')
# plt.legend()
# plt.show()
# plt.ion()

"""
backtest_engine.py
------------------
東証個別銘柄の日足データを対象にした、シグナルベースのバックテストエンジン。
- 買いのみ(ロング)
- 手数料: 0.1%(往復0.2%)
- 保有日数: 1, 5, 10, 20, 25日
- 検証シグナル: 9種
"""

import numpy as np
import pandas as pd

# ──────────────────────────────────────────
# 定数
# ──────────────────────────────────────────
HOLD_DAYS_LIST = [1, 5, 10, 20, 25]
COMMISSION = 0.001  # 片道 0.1%（往復 0.2%）


# ──────────────────────────────────────────
# テクニカル指標計算
# ──────────────────────────────────────────
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    日足DataFrameにテクニカル指標を追加して返す。
    必要列: open, high, low, close, volume
    """
    df = df.copy()

    # --- 列名を小文字に正規化 ---
    df.columns = [c.lower() for c in df.columns]

    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["volume"] if "volume" in df.columns else pd.Series(
        np.nan, index=df.index)

    # --- 移動平均 ---
    df["ma5"] = close.rolling(5).mean()
    df["ma20"] = close.rolling(20).mean()
    df["ma60"] = close.rolling(60).mean()

    # --- RSI(14) ---
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean()
    avg_loss = loss.ewm(com=13, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi14"] = 100 - (100 / (1 + rs))

    # --- MACD(12,26,9) ---
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    # --- ボリンジャーバンド(20, ±2σ) ---
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std(ddof=1)
    df["bb_upper"] = sma20 + 2 * std20
    df["bb_lower"] = sma20 - 2 * std20

    # --- ATR(14) ---
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    df["atr14"] = tr.rolling(14).mean()
    df["atr14_min20"] = df["atr14"].rolling(20).min()  # ボラ収縮判定用

    # --- 出来高の20日移動平均 ---
    df["vol_ma20"] = vol.rolling(20).mean()

    # --- 前日高値 ---
    df["prev_high"] = high.shift(1)

    return df


# ──────────────────────────────────────────
# シグナル定義
# ──────────────────────────────────────────
def _shifted_cond(cond_series: pd.Series) -> pd.Series:
    """シグナルは翌日エントリーのためシフト不要（エントリー判定はT日終値、エントリーはT+1日始値）"""
    return cond_series.fillna(False)


SIGNALS = [
    {
        "id":   "rsi_oversold",
        "name": "RSI過売（RSI<30）",
        "entry": lambda df: df["rsi14"] < 30,
    },
    {
        "id":   "macd_cross_up",
        "name": "MACDゴールデンクロス",
        "entry": lambda df: (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1)),
    },
    {
        "id":   "bb_lower_touch",
        "name": "ボリバン下限タッチ",
        "entry": lambda df: df["close"] < df["bb_lower"],
    },
    {
        "id":   "gc_ma5_20",
        "name": "ゴールデンクロス（MA5>MA20）",
        "entry": lambda df: (df["ma5"] > df["ma20"]) & (df["ma5"].shift(1) <= df["ma20"].shift(1)),
    },
    {
        "id":   "high_volume_up",
        "name": "出来高急増＋陽線",
        "entry": lambda df: (
            (df["volume"] > df["vol_ma20"] * 2) &
            (df["close"] > df["open"])
        ) if "volume" in df.columns else pd.Series(False, index=df.index),
    },
    {
        "id":   "atr_squeeze",
        "name": "ボラ収縮（ATRスクイーズ）",
        "entry": lambda df: df["atr14"] <= df["atr14_min20"],
    },
    {
        "id":   "prev_high_break",
        "name": "前日高値ブレイク＋MA20上",
        "entry": lambda df: (df["high"] > df["prev_high"]) & (df["close"] > df["ma20"]),
    },
    {
        "id":   "close_above_ma60",
        "name": "終値がMA60を上抜け",
        "entry": lambda df: (df["close"] > df["ma60"]) & (df["close"].shift(1) <= df["ma60"].shift(1)),
    },
    {
        "id":   "rsi_momentum",
        "name": "RSIモメンタム（30→50突破）",
        "entry": lambda df: (df["rsi14"] > 50) & (df["rsi14"].shift(1) <= 50) & (df["rsi14"].shift(5) < 40),
    },
]


# ──────────────────────────────────────────
# バックテスト実行（単一シグナル×単一保有日数）
# ──────────────────────────────────────────
def run_backtest(df: pd.DataFrame, signal: dict, hold_days: int) -> pd.DataFrame:
    """
    シグナル発生翌日の始値でエントリー → hold_days 日後の始値でエグジット。
    手数料往復 0.2% を差し引いたリターンを返す。

    Returns
    -------
    trades_df : pd.DataFrame
        columns: entry_date, entry_price, exit_date, exit_price, ret, ret_net
    """
    entry_mask = _shifted_cond(signal["entry"](df))

    trades = []
    entry_idx = None  # 現在保有中かどうか（インデックス整数）

    closes = df["close"].values
    opens = df.get("open", df["close"]).values  # openがない銘柄は closeで代替
    dates = df.index

    n = len(df)
    for i in range(n):
        if entry_idx is not None:
            # 保有中 → 保有期間チェック
            if i - entry_idx >= hold_days:
                exit_price = opens[i] if i < n else closes[i - 1]
                entry_price = opens[entry_idx]
                ret_gross = (exit_price - entry_price) / entry_price
                ret_net = ret_gross - 2 * COMMISSION
                trades.append({
                    "entry_date":  dates[entry_idx],
                    "entry_price": round(entry_price, 2),
                    "exit_date":   dates[i],
                    "exit_price":  round(exit_price, 2),
                    "ret":         round(ret_gross, 5),
                    "ret_net":     round(ret_net, 5),
                })
                entry_idx = None

        # エントリー判定（保有していないときのみ）
        if entry_idx is None and i + 1 < n and entry_mask.iloc[i]:
            entry_idx = i + 1  # 翌日エントリー

    return pd.DataFrame(trades)


# ──────────────────────────────────────────
# 統計集計
# ──────────────────────────────────────────
def summarize(trades_df: pd.DataFrame) -> dict:
    """トレードリストから各種統計を集計して返す。"""
    if trades_df is None or trades_df.empty:
        return {
            "trade_count": 0,
            "win_rate":    None,
            "expected_value": None,
            "profit_factor":  None,
            "avg_win":    None,
            "avg_loss":   None,
            "max_dd":     None,
            "sharpe":     None,
        }

    rets = trades_df["ret_net"]
    wins = rets[rets > 0]
    losses = rets[rets <= 0]

    win_rate = len(wins) / len(rets) if len(rets) > 0 else None
    ev = rets.mean()
    pf = (wins.sum() / abs(losses.sum())) if losses.sum() != 0 else np.inf
    avg_win = wins.mean() if not wins.empty else 0.0
    avg_loss = losses.mean() if not losses.empty else 0.0

    # 最大ドローダウン（累積リターンのピーク比）
    cum = (1 + rets).cumprod()
    rolling_max = cum.cummax()
    dd = (cum - rolling_max) / rolling_max
    max_dd = dd.min()

    # シャープ比（年率換算 / 252営業日）
    sharpe = (rets.mean() / rets.std() * np.sqrt(252)
              ) if rets.std() > 0 else None

    return {
        "trade_count":    int(len(rets)),
        "win_rate":       round(float(win_rate) * 100, 1) if win_rate is not None else None,
        "expected_value": round(float(ev) * 100, 3),   # %表示
        "profit_factor":  round(float(pf), 2) if pf != np.inf else None,
        "avg_win":        round(float(avg_win) * 100, 3),
        "avg_loss":       round(float(avg_loss) * 100, 3),
        "max_dd":         round(float(max_dd) * 100, 2) if max_dd is not None else None,
        "sharpe":         round(float(sharpe), 2) if sharpe is not None else None,
    }


# ──────────────────────────────────────────
# 全シグナル × 全保有日数 一括実行
# ──────────────────────────────────────────
def run_all(df: pd.DataFrame) -> pd.DataFrame:
    """
    全シグナル × 全保有日数 (HOLD_DAYS_LIST) のバックテストを実行し、
    サマリーをまとめた DataFrame を返す。

    Parameters
    ----------
    df : pd.DataFrame
        日足OHLCV DataFrame。列名は小文字(open/high/low/close/volume)想定。
        date 列またはDatetimeIndex を持つこと。

    Returns
    -------
    result_df : pd.DataFrame
        columns: signal_name, hold_days, trade_count, win_rate,
                 expected_value, profit_factor, avg_win, avg_loss, max_dd, sharpe
    """
    # インデックスをDatetimeIndexに
    df_ind = df.copy()
    if "date" in df_ind.columns:
        df_ind["date"] = pd.to_datetime(df_ind["date"])
        df_ind = df_ind.set_index("date")
    else:
        df_ind.index = pd.to_datetime(df_ind.index)

    df_ind = add_indicators(df_ind)

    rows = []
    for sig in SIGNALS:
        for hd in HOLD_DAYS_LIST:
            trades = run_backtest(df_ind, sig, hd)
            stats = summarize(trades)
            rows.append({
                "signal_id":      sig["id"],
                "signal_name":    sig["name"],
                "hold_days":      hd,
                **stats,
            })

    result_df = pd.DataFrame(rows)
    # 期待値降順ソート
    result_df = result_df.sort_values(
        "expected_value", ascending=False, na_position="last")
    return result_df


# ──────────────────────────────────────────
# スモークテスト（直接実行時）
# ──────────────────────────────────────────
if __name__ == "__main__":
    from get_yahooquery import get_stock_history
    print("7203（トヨタ）で動作確認中...")
    raw = get_stock_history("7203", period="1y", interval="1d").reset_index()
    result = run_all(raw)
    pd.set_option("display.max_rows", 60)
    pd.set_option("display.float_format", "{:.3f}".format)
    pd.set_option("display.width", 140)
    print(result.to_string(index=False))

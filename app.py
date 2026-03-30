import os
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, request
import pandas as pd
import numpy as np
from get_yahooquery import get_stock_history, get_financial_data, get_all_financial_data
from create_chart import create_candlestick, create_lineChart
from static.translations import COLUMN_TRANSLATIONS
from sqlite_rw import read_sqlite

app = Flask(__name__)


def get_stock_history_1d_from_db(symbol: str) -> pd.DataFrame:
    """
    public.prices テーブルから直近1年分の日足データを取得する。
    取得失敗・データなしの場合は空の DataFrame を返す。
    """
    try:
        import kabu_utils
        from sqlalchemy import text

        engine = kabu_utils.get_engine()
        query = text("""
            SELECT date, open, high, low, close, volume
            FROM public.prices
            WHERE symbol = :symbol
              AND date >= CURRENT_DATE - INTERVAL '1 year'
            ORDER BY date ASC
        """)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"symbol": str(symbol)})
        engine.dispose()

        if df.empty:
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"])
        df["MA5"] = df["close"].rolling(window=5).mean()
        df["MA20"] = df["close"].rolling(window=20).mean()
        df["MA60"] = df["close"].rolling(window=60).mean()
        return df
    except Exception as e:
        print(f"[DB] 日足データ取得エラー ({symbol}): {e}")
        return pd.DataFrame()


def prepare_for_chart(df: pd.DataFrame):
    """
    チャート用の前処理（空や列欠損を弾き、date列を正規化）
    """
    if df is None or df.empty:
        return None
    df = df.copy()
    cols_lower = {c.lower() for c in df.columns}
    need = {"open", "high", "low", "close"}
    if not need.issubset(cols_lower):
        return None
    if "date" not in df.columns:
        for c in ["Datetime", "datetime", "Date", "time", "Time"]:
            if c in df.columns:
                df = df.rename(columns={c: "date"})
                break
    if "date" not in df.columns:
        # indexに日時が入っているケースに対応
        if df.index.name and df.index.name.lower() in ["date", "datetime"]:
            df = df.reset_index().rename(columns={df.index.name: "date"})
        else:
            return None

    # date列を一律でdatetime64に変換しておく（date と datetime の比較エラー対策）
    try:
        df["date"] = pd.to_datetime(df["date"])
    except Exception:
        # 変換できない場合はチャート対象外とする
        return None
    return df


def compute_expected_ranges_1m(history_1d: pd.DataFrame):
    """
    過去の日足から、1ヶ月(20営業日)先の価格レンジを3つの方法で推定する。
    戻り値: dict(method_key -> {name, S0, lower, upper})
    """
    if history_1d is None or history_1d.empty:
        return {}

    df = history_1d.copy()
    # 終値列の名前の揺れに対応
    close_col = None
    for c in ["close", "Close", "adjclose", "Adj Close"]:
        if c in df.columns:
            close_col = c
            break
    if close_col is None:
        return {}

    close = pd.to_numeric(df[close_col], errors="coerce").dropna()
    if len(close) < 60:
        return {}

    S0 = float(close.iloc[-1])
    ranges = {}

    # --- 方法1: ヒストリカルボラ＋正規分布（30-70%程度の中央レンジ） ---
    r = np.log(close / close.shift(1)).dropna()
    if len(r) >= 20:
        sigma_daily = float(r.std())
        days = 20
        sigma_20 = sigma_daily * np.sqrt(days)
        # 30%〜70%程度のレンジに相当するz値（Φ(z)=0.7 → z≒0.524）を使用
        z = 0.524
        lower1 = S0 * np.exp(-z * sigma_20)
        upper1 = S0 * np.exp(z * sigma_20)
        ranges["method1"] = {
            "name": "方法1: ヒストリカルボラ(正規,30-70%)",
            "S0": S0,
            "lower": lower1,
            "upper": upper1,
        }

    # --- 方法2: 過去1ヶ月リターン分布からのパーセンタイル（30-70%） ---
    if len(close) >= 40:
        r20 = np.log(close / close.shift(20)).dropna()
        if not r20.empty:
            p30 = float(r20.quantile(0.30))
            p70 = float(r20.quantile(0.70))
            lower2 = S0 * np.exp(p30)
            upper2 = S0 * np.exp(p70)
            ranges["method2"] = {
                "name": "方法2: 過去1ヶ月リターン(30-70%)",
                "S0": S0,
                "lower": lower2,
                "upper": upper2,
            }

    # --- 方法3: ブートストラップシミュレーション（30-70%） ---
    if len(r) >= 40:
        n_sims = 2000
        days = 20
        sims = []
        r_values = r.values
        for _ in range(n_sims):
            sampled = np.random.choice(r_values, size=days, replace=True)
            ST = S0 * np.exp(sampled.sum())
            sims.append(ST)
        sims = np.array(sims)
        lower3 = float(np.percentile(sims, 30))
        upper3 = float(np.percentile(sims, 70))
        ranges["method3"] = {
            "name": "方法3: ブートストラップ(30-70%)",
            "S0": S0,
            "lower": lower3,
            "upper": upper3,
        }

    return ranges


def fetch_data_from_api(symbol: str):
    """
    シンボルから株価・財務データをまとめて取得する。
    将来、SQLiteキャッシュに戻すときもここを差し替えるだけで済む。
    """
    errors: list[str] = []
    results: dict[str, pd.DataFrame] = {}

    def retry(func, name: str, retries: int = 3, delay: float = 1.0):
        last_exc: Exception | None = None
        for i in range(retries):
            try:
                return func()
            except Exception as e:
                last_exc = e
                if i < retries - 1:
                    time.sleep(delay)
        raise last_exc  # type: ignore[misc]

    def safe_call(name: str, func):
        try:
            results[name] = retry(func, name)
        except Exception as e:
            results[name] = pd.DataFrame()
            label = {
                "history_1d": "日足データ",
                "history_5m": "5分足データ",
                "history_1mo": "月足データ",
                "financial": "財務データ",
                "financial_all": "詳細財務データ",
            }.get(name, name)
            errors.append(f"{label}の取得に失敗しました: {e}")

    # history_1d は PostgreSQL から取得（その他はYahoo Finance API）
    safe_call("history_1d", lambda: get_stock_history_1d_from_db(symbol))

    # Web API呼び出しを並列化して待ち時間を短縮しつつ、各APIはリトライする
    # NOTE: history_1d は上の get_stock_history_1d_from_db() で PostgreSQL から取得済みのため、
    #       ここで API から再取得すると後勝ちで上書きされるバグが発生する。
    #       DB取得を優先するためコメントアウト。API取得に戻す場合は上の safe_call("history_1d", ...) を削除すること。
    with ThreadPoolExecutor(max_workers=4) as ex:
        # ex.submit(
        #     safe_call,
        #     "history_1d",
        #     lambda: get_stock_history(
        #         symbol, period="1y", interval="1d").reset_index(),
        # )
        ex.submit(
            safe_call,
            "history_5m",
            # 負荷軽減のため60d→20dに短縮（必要に応じて調整）
            lambda: get_stock_history(
                symbol, period="60d", interval="5m").reset_index(),
        )
        ex.submit(
            safe_call,
            "history_1mo",
            # 必要ならperiodを短くすることも可能
            lambda: get_stock_history(
                symbol, period="max", interval="1mo").reset_index(),
        )
        ex.submit(
            safe_call,
            "financial",
            lambda: get_financial_data(symbol).reset_index(),
        )
        ex.submit(
            safe_call,
            "financial_all",
            lambda: get_all_financial_data(symbol).reset_index(),
        )

    return (
        {
            "history_1d": results.get("history_1d", pd.DataFrame()),
            "history_5m": results.get("history_5m", pd.DataFrame()),
            "history_1mo": results.get("history_1mo", pd.DataFrame()),
            "financial": results.get("financial", pd.DataFrame()),
            "financial_all": results.get("financial_all", pd.DataFrame()),
        },
        errors,
    )


def build_financial_tables(financial_data: pd.DataFrame, all_financial_data: pd.DataFrame):
    """
    財務データ用のHTMLテーブルと、生データテーブルHTMLを生成する。
    """
    financial_html = ""
    financial_data_raw_html = ""

    if financial_data is None or financial_data.empty:
        return financial_html, financial_data_raw_html

    # 列名を日本語に変換
    financial_data = financial_data.rename(columns=COLUMN_TRANSLATIONS)
    if all_financial_data is not None and not all_financial_data.empty:
        all_financial_data = all_financial_data.rename(
            columns=COLUMN_TRANSLATIONS)

    # 生の財務データをHTMLに変換
    if all_financial_data is not None and not all_financial_data.empty:
        financial_data_raw_html = all_financial_data.to_html(
            classes="table table-striped table-hover table-sm"
        )

    # 数値のフォーマットを設定
    for col in financial_data.columns:
        if pd.api.types.is_numeric_dtype(financial_data[col]):
            financial_data[col] = financial_data[col].apply(
                lambda x: f"{x:,.2f}" if pd.notnull(x) else "N/A"
            )

    # 列を3つのグループに分ける
    columns = list(financial_data.columns)
    group_size = (len(columns) + 2) // 3  # 3つのグループに均等に分割

    for i in range(0, len(columns), group_size):
        group_columns = columns[i: i + group_size]
        group_data = financial_data[group_columns]
        financial_html += group_data.to_html(
            classes="table table-striped table-hover table-sm",
            index=False,
        )
        financial_html += '<div class="mb-4"></div>'  # グループ間に余白を追加

    return financial_html, financial_data_raw_html


def extract_target_prices(financial_data: pd.DataFrame):
    """
    アナリスト目標株価系の列をdictにまとめる。
    """
    if financial_data is None or financial_data.empty:
        return {}
    return {
        "targetHighPrice": financial_data["targetHighPrice"].iloc[0]
        if "targetHighPrice" in financial_data.columns
        else None,
        "targetLowPrice": financial_data["targetLowPrice"].iloc[0]
        if "targetLowPrice" in financial_data.columns
        else None,
        "targetMeanPrice": financial_data["targetMeanPrice"].iloc[0]
        if "targetMeanPrice" in financial_data.columns
        else None,
        "targetMedianPrice": financial_data["targetMedianPrice"].iloc[0]
        if "targetMedianPrice" in financial_data.columns
        else None,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    table_html = ""  # テーブルのHTMLを初期化
    chart_html = ""  # チャートのHTMLを初期化
    chart_html2 = ""  # チャートのHTMLを初期化
    chart_html3 = ""  # チャートのHTMLを初期化
    linechart_html3 = ""  # チャートのHTMLを初期化
    symbol = ""  # symbolを初期化
    financial_html = ""  # 財務データのHTMLを初期化
    financial_data_raw_html = ""  # 生の財務データのHTMLを初期化
    show_raw_data = False  # デフォルトで非表示
    errors = []  # 画面に出すメッセージ
    expected_ranges = {}  # 1ヶ月レンジ推定結果

    if request.method == "POST":
        symbol = (request.form.get("symbol") or "").strip()
        show_raw_data = request.form.get(
            "show_raw_data", "false") == "true"  # チェックボックスの状態を取得

        if not symbol:
            errors.append("銘柄コードを入力してください。")
            return render_template(
                "index.html",
                plot=False,
                table_html=table_html,
                chart_html=chart_html,
                chart_html2=chart_html2,
                chart_html3=chart_html3,
                linechart_html3=linechart_html3,
                financial_html=financial_html,
                financial_data_raw_html=financial_data_raw_html,
                show_raw_data=show_raw_data,
                symbol=symbol,
                errors=errors,
            )

        # --- データ取得 ---
        data_dict, fetch_errors = fetch_data_from_api(symbol)
        errors.extend(fetch_errors)
        history_data = data_dict["history_1d"]
        history_data2 = data_dict["history_5m"]
        history_data3 = data_dict["history_1mo"]
        financial_data = data_dict["financial"]
        all_financial_data = data_dict["financial_all"]

        # 目標株価のデータを準備
        target_prices = extract_target_prices(financial_data)

        # 1ヶ月先レンジ（3つの方法）の計算（history_1dベース）
        expected_ranges = compute_expected_ranges_1m(history_data)
        # 5分足チャート用にレンジラインも渡す
        target_prices_5m = dict(target_prices) if target_prices else {}
        if expected_ranges:
            m1 = expected_ranges.get("method1")
            m2 = expected_ranges.get("method2")
            m3 = expected_ranges.get("method3")
            # lower / upper だけ水平線で描画 (現在値S0は数値表示に回す)
            if m1:
                target_prices_5m["m1_lower"] = m1["lower"]
                target_prices_5m["m1_upper"] = m1["upper"]
            if m2:
                target_prices_5m["m2_lower"] = m2["lower"]
                target_prices_5m["m2_upper"] = m2["upper"]
            if m3:
                target_prices_5m["m3_lower"] = m3["lower"]
                target_prices_5m["m3_upper"] = m3["upper"]

        # チャート生成前に安全化
        chart1_df = prepare_for_chart(history_data)
        chart2_df = prepare_for_chart(history_data2)
        chart3_df = prepare_for_chart(history_data3)

        chart_html = create_candlestick(
            chart1_df, symbol, target_prices) if chart1_df is not None else ''
        # 5分足チャートには1ヶ月レンジも重ねて表示
        chart_html2 = create_candlestick(
            chart2_df, symbol, target_prices_5m) if chart2_df is not None else ''
        chart_html3 = create_candlestick(
            chart3_df, symbol, target_prices) if chart3_df is not None else ''
        linechart_html3 = create_lineChart(
            chart3_df, symbol) if chart3_df is not None else ''

        if history_data is not None and not history_data.empty:
            # データを日付でソートし、順序を逆にする
            if "date" in history_data.columns:
                # date列を一律でdatetime64に変換（date と datetime の混在対策）
                try:
                    history_data = history_data.copy()
                    history_data["date"] = pd.to_datetime(history_data["date"])
                    history_data = history_data.sort_values(
                        "date", ascending=False)
                except Exception:
                    # 変換に失敗した場合はインデックスでフォールバック
                    history_data = history_data.sort_index(ascending=False)
            else:
                history_data = history_data.sort_index(ascending=False)
            table_html = history_data.to_html(
                classes="table table-striped table-hover table-sm", index=True
            )
        else:
            if not fetch_errors:  # APIエラーでなく純粋にデータが空
                errors.append("指定した銘柄の株価データが見つかりませんでした。")

        if all_financial_data is not None and not all_financial_data.empty:
            if "asOfDate" in all_financial_data.columns:
                all_financial_data = all_financial_data.sort_values(
                    "asOfDate", ascending=False
                )

        # 財務データをHTMLテーブルに変換
        financial_html, financial_data_raw_html = build_financial_tables(
            financial_data, all_financial_data
        )

        any_plot = any(
            [
                chart_html,
                chart_html2,
                chart_html3,
                linechart_html3,
                table_html,
                financial_html,
                financial_data_raw_html,
            ]
        )
        return render_template(
            "index.html",
            plot=any_plot,
            table_html=table_html,
            chart_html=chart_html,
            chart_html2=chart_html2,
            chart_html3=chart_html3,
            linechart_html3=linechart_html3,
            financial_html=financial_html,
            financial_data_raw_html=financial_data_raw_html,
            show_raw_data=show_raw_data,
            symbol=symbol,
            errors=errors,
            expected_ranges=expected_ranges,
        )

    return render_template(
        "index.html",
        plot=False,
        table_html=table_html,
        chart_html=chart_html,
        chart_html2=chart_html2,
        chart_html3=chart_html3,
        linechart_html3=linechart_html3,
        financial_html=financial_html,
        financial_data_raw_html=financial_data_raw_html,
        show_raw_data=show_raw_data,
        symbol=symbol,
        errors=errors,
        expected_ranges=expected_ranges,
    )


if __name__ == "__main__":
    app.run(debug=True)

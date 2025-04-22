from yahooquery import Ticker
import pandas as pd
import sqlite3
import datetime
#yahooqueryから株価データを取得する
def get_financial_price(stock_code): 
    try:
        ticker = Ticker(stock_code + '.T')
        # 辞書型データを展開して必要なデータのみを取得
        financial_data = ticker.financial_data
        print("financial_dataの構造:", financial_data)
        df = pd.DataFrame(financial_data).T  # .Tで転置して行と列を入れ替える
        df['Date'] = datetime.date.today()
        print("作成されたDataFrame:")
        print(df.head())
        print("\n列名:", df.columns.tolist())
        print("\nインデックス:", df.index.tolist())
        # SQLiteに保存
        with sqlite3.connect(db_path) as conn:
            df.to_sql('financial_price', conn, if_exists='append', index=True)
            print(f"銘柄コード {stock_code} のデータを保存しました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

def get_stock_codes_and_process(db_path):
    """
    SQLiteのテーブル 'taishakumeigara' から銘柄コードを取得し、
    各銘柄コードに対して関数 'process_stock_code' を繰り返し実行する。

    Parameters:
        db_path (str): SQLiteデータベースのパス。
    """
    try:
        # データベースに接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 銘柄コードを取得するSQLクエリ
        query = 'SELECT "銘柄コード" FROM taishakumeigara WHERE "市場区分/商品区分" != "ETF"  AND "信用区分" = "貸借銘柄"'
        cursor.execute(query)

        # 結果を1つずつ取得して関数に渡す
        for row in cursor.fetchall():
            stock_code = row[0]
            get_financial_price(stock_code)

        # 接続を閉じる
        conn.close()
        print("すべての銘柄コードを処理しました。")

    except sqlite3.Error as e:
        print(f"SQLiteエラーが発生しました: {e}")

if __name__ == '__main__':
            # SQLiteデータベースのパス
    db_path = "C:\\Users\\Owner\\Desktop\\FlaskPractice\\stock_data.db"
    
    # code = get_financial_price('1377')
    # print(code)
    # print('成功しました')
    start_time = datetime.datetime.now()
    print(start_time)
    # 銘柄コードを取得して関数を実行
    get_stock_codes_and_process(db_path)
    
    end_time = datetime.datetime.now()
    print(end_time)
    
    delta = end_time - start_time
    print(delta)
    


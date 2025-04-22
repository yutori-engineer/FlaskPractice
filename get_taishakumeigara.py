import requests
import pandas as pd
import sqlite3
from io import BytesIO

def download_excel(url):
    """
    インターネット上のExcelファイルをダウンロードしてDataFrameに変換する。

    Parameters:
        url (str): ExcelファイルのURL。

    Returns:
        pd.DataFrame: Excelファイルのデータ。
    """
    response = requests.get(url)
    response.raise_for_status()  # ダウンロードに失敗した場合はエラーをスロー
    excel_data = BytesIO(response.content)
    df = pd.read_excel(excel_data)

    # 1行目を削除して2行目を列名に設定
    df.columns = df.iloc[0]
    df = df.drop(0)
    
    return df

def save_to_sqlite(df, db_path, table_name):
    """
    DataFrameをSQLiteデータベースに保存する。

    Parameters:
        df (pd.DataFrame): 保存するデータ。
        db_path (str): SQLiteデータベースのパス。
        table_name (str): テーブル名。
    """
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    print(f"データがSQLiteデータベース '{db_path}' のテーブル '{table_name}' に保存されました。")

if __name__ == "__main__":
    # インターネット上のExcelファイルのURL
    url = "https://www.jpx.co.jp/listing/others/margin/tvdivq0000000od2-att/20241202_list.xlsx"

    # SQLiteデータベースファイルのパス
    db_path = "C:\\Users\\Owner\\Desktop\\FlaskPractice\\stock_data.db"

    # ダウンロードしてDataFrameに変換
    df = download_excel(url)

    # SQLiteに書き込む
    save_to_sqlite(df, db_path, "taishakumeigara")

import requests
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from sqlite_rw import save_to_sqlite

def download_excel(url):
    # ページのHTMLを取得
    response = requests.get(url)
    # ステータスコードが200でない場合、例外を発生させる
    response.raise_for_status()
    # HTMLをパース
    soup = BeautifulSoup(response.content, "html.parser")

    # エクセルファイルへのリンクを抽出
    excel_links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.lower().endswith((".xls", ".xlsx")):
            full_url = urljoin(url, href)
            excel_links.append(full_url)

    # 結果を表示
    link = ''
    if excel_links:
        print("エクセルファイルのリンク:")
        for link in excel_links:
            print(link)
    else:
        print("エクセルファイルのリンクが見つかりませんでした。")
    
    #エクセルファイルのリンク先を抽出    
    response = requests.get(link)
    # ダウンロードに失敗した場合はエラーをスロー
    response.raise_for_status()  

    excel_data = BytesIO(response.content)
    df = pd.read_excel(excel_data)

    # 1行目を削除して2行目を列名に設定
    df.columns = df.iloc[0]
    df = df.drop(0)
    
    return df

if __name__ == "__main__":
    # JPXのマージン取引関連ページのURL
    url = "https://www.jpx.co.jp/listing/others/margin/index.html"
    # SQLiteデータベースファイルのパス
    db_path = "C:\\Users\\Owner\\Desktop\\FlaskPractice\\stock_data.db"

    # ダウンロードしてDataFrameに変換
    df = download_excel(url)

    # SQLiteに書き込む
    save_to_sqlite(df, db_path, "taishakumeigara")



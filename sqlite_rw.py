import sqlite3

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
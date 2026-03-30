"""
database.py — Tech0 Search v1.0
SQLite DB への接続・初期化・CRUD 操作を一元管理する。
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# DB ファイルのパス（data/ サブフォルダに保存する）
DB_PATH = Path("data/tech0_search.db")


def get_connection():
    """
    DB への接続を取得する。

    row_factory を設定することで、行データを辞書のように扱える。
    data/ フォルダが存在しない場合は自動で作成する。
    """
    DB_PATH.parent.mkdir(exist_ok=True)   # data/ フォルダがなければ作る
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row        # 行データを辞書のように扱う
    return conn


def init_db():
    """
    schema.sql を読み込んで DB を初期化する。

    CREATE TABLE IF NOT EXISTS を使っているので、
    すでにテーブルが存在する場合は何もしない。
    """
    conn = get_connection()
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())    # SQL ファイルをまとめて実行する
    conn.commit()
    conn.close()


def insert_document(document: dict) -> int:    #pageをdocumentに変更
    """
    ドキュメント情報を DB に登録する。

    INSERT OR REPLACE：同じ URL のデータがあれば上書き、なければ新規追加する。
    これにより「同じページを再クロールしたときに最新データに更新できる」。

    Args:
        document: ドキュメント情報の辞書（crawl_url() の返り値と同形式）

    Returns:
        登録された行の id
    """
    conn = get_connection()
    cursor = conn.cursor() 

    cursor.execute("""
        INSERT OR REPLACE INTO documents                        
            (title, department, author, category, keywords, full_text, word_count)  

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        document["title"],              #pageからdocumentに変更
        document.get("department", ""), #pageからdocumentに変更
        document.get("full_text", ""),  #pageからdocumentに変更
        document.get("author", ""),     #pageからdocumentに変更
        document.get("category", ""),   #pageからdocumentに変更
        document.get("word_count", 0),  #pageからdocumentに変更
        document.get("keywords", "")    #pageからdocumentに変更
        
    ))

    document_id = cursor.lastrowid    # 登録された行の id を取得する #pageからdocumentに変更
    conn.commit()
    conn.close()
    return document_id      #pageからdocumentに変更


def get_all_documents() -> list:
    """全ドキュメントを登録日時の新しい順で取得する。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]    # sqlite3.Row を辞書に変換して返す



    """
    log_search()を丸ごと削除。この下のpassも削除
    """
    
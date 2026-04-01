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

        VALUES (?, ?, ?, ?, ?, ?, ?)
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




def insert_post(text: str, name: str, anonymous: bool) -> int:
    """
    投稿を DB に登録する。

    Args:
        text: 投稿本文
        name: 投稿者名
        anonymous: 匿名フラグ（True=匿名）

    Returns:
        登録された投稿のposts.id
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 匿名フラグを整数に変換（SQLiteはboolをそのまま保存できないため）
    if anonymous:
        anonymous_int = 1 
    else:
        anonymous_int = 0

    cursor.execute("""  
        INSERT INTO posts
            (text, name, anonymous)
        VALUES (?, ?, ?)
    """, (text, name, anonymous_int))

    post_id = cursor.lastrowid    # 登録された行の id を取得できる
    conn.commit()
    conn.close()
    return post_id

def get_all_posts() -> list:
    """全投稿を登録日時の新しい順で取得する。"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY posted_at DESC")
    rows = cursor.fetchall() # 直前に実行したSQLの結果を全行まとめてリストで取得する
    conn.close()
    return [dict(row) for row in rows]    

def add_like(post_id) -> int:
    """
    指定した投稿のいいねを１件追加する。

    Args:
        post_id: いいねする投稿のid

    Returns:
        いいね数が追加されたlikesテーブルのid
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""  
        INSERT INTO likes
            (post_id)
        VALUES (?)
    """, (post_id, ))

    like_id = cursor.lastrowid    # 登録された行の id を取得できる
    conn.commit()
    conn.close()
    return like_id

def get_like_count(post_id: int) -> int:
    """
    指定した投稿のいいね数を返す。

    Args:
        post_id: いいね数を取得するの投稿ID

    Returns:
        いいね数
    """
    conn = get_connection()
    cursor = conn.cursor()

    # post_id が一致するレコード数の合計 = post_idをもつ投稿のいいね数
    cursor.execute("""
        SELECT COUNT(*) FROM likes WHERE post_id = ?
    """, (post_id,))

    count = cursor.fetchone()[0]    # COUNT(*) の値を取り出す
    conn.close()
    return count

def get_hot_posts() -> list:
    """
    いいね数の多い順に全投稿を返す（Hotランキング用）。

    Returns:
        投稿の辞書リスト。各辞書に like_count キーが追加されている。
    """
    conn = get_connection()
    cursor = conn.cursor()

    # LEFT JOIN でpostsテーブルとlikesテーブルを結合していいね数を集計 → 多い順に並べる
    # いいねが0件の投稿も表示するため LEFT JOIN を使う
    cursor.execute("""
        SELECT
            posts.id,
            posts.text,
            posts.name,
            posts.anonymous,
            posts.posted_at,
            COUNT(likes.id) AS like_count
        FROM posts
        LEFT JOIN likes ON posts.id = likes.post_id
        GROUP BY posts.id
        ORDER BY like_count DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append(dict(row))
    return result

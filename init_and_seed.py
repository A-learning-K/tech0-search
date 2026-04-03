"""
init_and_seed.py — Tech0 Search v1.0
DBを初期化してサンプルデータを投入する。
デプロイ前に1回だけ実行する。

実行方法：
    python init_and_seed.py
"""

import json
from database import init_db, get_connection, insert_document


def load_documents():
    """
    techzeron_documents_final.json からドキュメントを投入する。
    JSONファイルの読み込みとcursor.execute() の中身を埋める。
    """
    # ①JSONファイルを読み込む
    # ↓ここに埋める（下のload_posts()を参考に記載してみてください）
    with open("data/techzeron_documents_final.json", "r", encoding="utf-8") as f:
         documents = json.load(f) 

    conn = get_connection()
    cursor = conn.cursor()

    # ②既存データを全件削除してから投入する
    # cursor.execute("")  ← SQL文を中に記載する 
    cursor.execute("DELETE FROM documents") # documentsテーブルのデータを全件削除するSQL文
    conn.commit() 
    conn.close()  #接続を閉じる（この後 insert_document() 内で再度接続するため）

    # 1件ずつドキュメントを投入する
    count = 0
    for doc in documents:  
        # insert_document() を呼ぶ
        # JSONのキー名とDBのカラム名が違う箇所があるので注意←（Q)確かにそうです、なぜ？
        #         tags（JSON） → keywords（DB）
        #         content（JSON） → full_text（DB）
        # ③↓ここを埋める（insert_document に渡す辞書を作って呼び出す）
        doc_data = {
            'title': doc['title'],
            'department': doc['department'],
            'author': doc['author'],
            'category': doc['category'],
            'keywords': doc['tags'],        # tags を keywords に変換
            'created_at': doc['created_at'],
            'updated_at': doc['updated_at'],
            'word_count': doc['word_count'],
            'full_text': doc['content']      # content を full_text に変換
        }  

        insert_document(doc_data)
        count += 1

    print(f"✅ documents投入完了：{count}件")


def load_posts():
    """seed_posts.json から投稿・いいねデータを投入する。"""
    # JSONファイルを読み込む
    with open("data/seed_posts.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_connection()
    cursor = conn.cursor()

    # 既存データを全件削除する（likesはpostsに依存しているので先に消す）
    cursor.execute("DELETE FROM likes")
    cursor.execute("DELETE FROM posts")

    # postsを1件ずつ投入する
    count_posts = 0
    for post in data["posts"]:
        cursor.execute("""
            INSERT INTO posts (title, category, text, name, anonymous, posted_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                post["title"],
                post["category"],
                post["text"],
                post["name"],
                post["anonymous"],
                post["posted_at"],
            ))        
        count_posts += 1

    conn.commit()
    print(f"✅ posts投入完了：{count_posts}件")

    # likesを1件ずつ投入する
    count_likes = 0
    for like in data["likes"]:
        cursor.execute("""
            INSERT INTO likes (post_id, liked_at)
            VALUES (?, ?)
        """, (
            like["post_id"],
            like["liked_at"],
        ))
        count_likes += 1

    conn.commit()
    conn.close()
    print(f"✅ likes投入完了：{count_likes}件")


if __name__ == "__main__":
    print("=== DB初期化＆シードデータ投入開始 ===")
    init_db()           # テーブルを作る（schema.sqlを読み込む）
    load_documents()    # documentsテーブルにデータを投入する
    load_posts()        # posts・likesテーブルにデータを投入する
    print("=== 完了 ===")
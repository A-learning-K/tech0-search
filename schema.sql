-- schema.sql
-- Tech0 Search v1.0 データベース設計

-- documentsテーブル（メイン）
-- UNIQUE 制約：同じ URL は重複して登録できない  



CREATE TABLE IF NOT EXISTS documents (             -- pages→documents に変更
    id          INTEGER PRIMARY KEY AUTOINCREMENT, -- 通し番号 #そのまま
    title       TEXT NOT NULL,                     -- ドキュメントのタイトル　-- そのまま
    department  TEXT,                              -- 作成部署 -- description→department に変更
    author      TEXT,                              -- 作成者名　-- そのまま
    category    TEXT,                              -- 文書の種類　-- そのまま
    keywords    TEXT,                              -- 検索用キーワード（カンマ区切り）
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 作成日　-- TextよりDATETIMEが良さげ
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,   -- 最終更新日　-- TextよりDATETIMEが良さげ
    word_count  INTEGER DEFAULT 0,                 -- 文字カウント。追記しました
    full_text   TEXT                               -- 本文（TF-IDFの検索対象メイン）  
);                                                 

-- keywordsテーブル（TF-IDFスコア保存）
-- page_id が削除されたら自動的にキーワードも削除される（ON DELETE CASCADE）
CREATE TABLE IF NOT EXISTS keywords (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,     -- page→document に変更
    keyword     TEXT NOT NULL,
    tf_score    REAL DEFAULT 0.0,
    tfidf_score REAL DEFAULT 0.0,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 検索ログテーブル（発展用）
CREATE TABLE IF NOT EXISTS search_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    query         TEXT NOT NULL,
    results_count INTEGER DEFAULT 0,
    user_id       TEXT,
    searched_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- クリックログテーブル（発展用）--テーブルを丸ごと削除しました

-- インデックス作成（検索を高速化する）
CREATE INDEX IF NOT EXISTS idx_keyword    ON keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_document_id    ON keywords(document_id);   -- page_id→document_id に変更
CREATE INDEX IF NOT EXISTS idx_search_query ON search_logs(query);
CREATE INDEX IF NOT EXISTS idx_search_date  ON search_logs(searched_at);

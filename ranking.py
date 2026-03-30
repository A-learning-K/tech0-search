"""
ranking.py — Tech0 Search v1.0
TF-IDF ベースの検索エンジン（SearchEngine クラス）を提供する。
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List
from collections import Counter
import math
from datetime import datetime


# ==========================================================
# ① 学習用：TF / IDF を手実装するパート
# ==========================================================

def tokenize(text: str) -> list:
    """
    とても簡易的なトークン化
    小文字化して空白で分割する
    """
    return text.lower().split()


def calc_tf(tokens: list) -> dict:
    """
    TF (Term Frequency) を計算する
    各単語が、その文書内でどれくらい出てくるかを表す

    例:
        ["python", "search", "python"]
        -> {"python": 2/3, "search": 1/3}
    """
    tf = {}
    total_terms = len(tokens)

    if total_terms == 0:
        return tf

    counts = Counter(tokens)
    for term, count in counts.items():
        tf[term] = count / total_terms

    return tf


def calc_idf(docs_tokens: list) -> dict:
    """
    IDF (Inverse Document Frequency) を計算する
    多くの文書に出る単語は低く、珍しい単語は高くする

    式:
        idf = log(総文書数 / その単語を含む文書数) + 1
    """
    idf = {}
    total_docs = len(docs_tokens)

    if total_docs == 0:
        return idf

    # 全文書に出てくる単語を集める
    all_terms = set()
    for tokens in docs_tokens:
        all_terms.update(tokens)

    for term in all_terms:
        doc_count = sum(1 for tokens in docs_tokens if term in tokens)
        idf[term] = math.log(total_docs / doc_count) + 1

    return idf


def calc_tfidf(tf: dict, idf: dict) -> dict:
    """
    TF-IDF を計算する
    """
    tfidf = {}
    for term, tf_value in tf.items():
        tfidf[term] = tf_value * idf.get(term, 0)
    return tfidf


def cosine_sim_dict(vec1: dict, vec2: dict) -> float:
    """
    dict 形式のベクトル同士でコサイン類似度を計算する
    """
    all_terms = set(vec1.keys()) | set(vec2.keys())

    dot = sum(vec1.get(term, 0) * vec2.get(term, 0) for term in all_terms)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)


def manual_search(query: str, documents: list, top_n: int = 20) -> list:
    """
    手実装版の簡易検索
    calc_tf / calc_idf を使って TF-IDF を作り、
    コサイン類似度で検索する
    """
    if not query.strip() or not documents:
        return []

    # 各文書から検索対象テキストを作る
    docs = []
    for document in documents:
        kw = document.get("keywords", "") or ""
        if isinstance(kw, str):
            kw_list = [k.strip() for k in kw.split(",") if k.strip()]
        else:
            kw_list = kw

        text = " ".join([
            (document.get("title", "") + " ") * 3,
            (document.get("department", "") + " ") * 2,
            (document.get("content", "") + " "),
            (" ".join(kw_list) + " ") * 2,
        ])
        docs.append(text)

    # トークン化
    docs_tokens = [tokenize(doc) for doc in docs]
    query_tokens = tokenize(query)

    # IDF を計算
    idf = calc_idf(docs_tokens + [query_tokens])

    # クエリの TF-IDF
    query_tf = calc_tf(query_tokens)
    query_tfidf = calc_tfidf(query_tf, idf)

    results = []
    for idx, tokens in enumerate(docs_tokens):
        document_tf = calc_tf(tokens)
        document_tfidf = calc_tfidf(document_tf, idf)

        score = cosine_sim_dict(query_tfidf, document_tfidf)

        if score > 0.01:
            document = documents[idx].copy()
            document["relevance_score"] = round(score * 100, 1)
            results.append(document)

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:top_n]


# ==========================================================
# ②〜④ 本番用：ライブラリ版 + クラス化
# ==========================================================

class SearchEngine:
    """TF-IDFベースの検索エンジン"""

    def __init__(self):
        # TF-IDF ベクトライザーを初期化する
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),  # ユニグラムとバイグラムを使う
            min_df=1,
            max_df=0.95,
            sublinear_tf=True
        )
        self.tfidf_matrix = None
        self.documents = []
        self.is_fitted = False

    def build_index(self, documents: list):
        """
        全文書の TF-IDF インデックスを構築する
        """
        if not documents:
            return

        self.documents = documents

        corpus = []
        for document in documents:
            kw = document.get("keywords", "") or ""
            if isinstance(kw, str):
                kw_list = [k.strip() for k in kw.split(",") if k.strip()]
            else:
                kw_list = kw

            text = " ".join([
                (document.get("title", "") + " ") * 3,
                (document.get("department", "") + " ") * 2,
                (document.get("content", "") + " "),
                (" ".join(kw_list) + " ") * 2,
            ])
            corpus.append(text)

        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_fitted = True

    def search(self, query: str, top_n: int = 20) -> list:
        """
        TF-IDF ベースの検索を実行する
        """
        if not self.is_fitted or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        results = []
        for idx, base_score in enumerate(similarities):
            if base_score > 0.01:
                document = self.documents[idx].copy()
                final_score = self._calculate_final_score(document, base_score, query)

                document["relevance_score"] = round(float(final_score) * 100, 1)
                document["base_score"] = round(float(base_score) * 100, 1)
                results.append(document)

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_n]

    def _calculate_final_score(self, document: dict, base_score: float, query: str) -> float:
        """
        複数の要素を組み合わせて最終スコアを計算する
        """
        score = base_score
        query_lower = query.lower()

        title = document.get("title", "").lower()
        if query_lower == title:
            score *= 1.8
        elif query_lower in title:
            score *= 1.4

        keywords = document.get("keywords", [])
        if isinstance(keywords, str):
            keywords = keywords.split(",")
        keywords_lower = [k.strip().lower() for k in keywords]
        if query_lower in keywords_lower:
            score *= 1.3

        timestamp = document.get("updated_at") or document.get("created_at") or ""
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                days_old = (datetime.now() - dt.replace(tzinfo=None)).days
                if days_old <= 90:
                    recency_bonus = 1 + (0.2 * (90 - days_old) / 90)
                    score *= recency_bonus
            except Exception:
                pass

        word_count = document.get("word_count", 0)
        if word_count < 50:
            score *= 0.7
        elif word_count > 10000:
            score *= 0.85

        return score


# ── シングルトン管理 ──────────────────────────────────────────

_engine = None


def get_engine() -> SearchEngine:
    """検索エンジンのシングルトンを取得する"""
    global _engine
    if _engine is None:
        _engine = SearchEngine()
    return _engine


def rebuild_index(documents: List[dict]):
    """インデックスを再構築する"""
    engine = get_engine()
    engine.build_index(documents)
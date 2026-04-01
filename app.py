"""
app.py — Tech0 Search v1.0（完成版）
Streamlit アプリ本体。検索・クローラー・一覧の3タブ構成。
"""

import re
import streamlit as st
from database import init_db, get_all_documents, insert_document, insert_post, get_all_posts, add_like, get_like_count, get_hot_posts
from ranking import get_engine, rebuild_index
from crawler import crawl_url

# ── 定数 ──────────────────────────────────────────────────────
OYOBIDASHI_THRESHOLD = 3  # お呼び出し閾値（デモ用に低め設定。本番は100）

# アプリ起動時に DB を初期化する（テーブルが未作成なら作る）
init_db()

st.set_page_config(
    page_title="Tech0 Search v1.0",
    page_icon="🔍",
    layout="wide",
)


# ── 全体デザイン ───────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

/* ── サイドバー（ピンク系） ── */
[data-testid="stSidebar"] {
    background: #FBEAF0 !important;
    border-right: 1px solid #F4C0D1 !important;
}
[data-testid="stSidebar"] * { color: #72243E !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #3C3489 !important; font-size: 1.8rem !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    background: #D4537E !important; color: #fff !important;
    border: none !important; border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
    background: #993556 !important;
}

/* ── タブ（パープル系） ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    border-bottom: 1px solid #CECBF6; background: transparent; gap: 0;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-size: 0.82rem; color: #AFA9EC;
    padding: 8px 18px; border-bottom: 2px solid transparent; background: transparent;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: #534AB7 !important;
    border-bottom: 2px solid #7F77DD !important;
    background: transparent !important;
}

/* ── 検索入力（パープル） ── */
[data-testid="stTextInput"] input {
    background: #EEEDFE !important;
    border: 1.5px solid #CECBF6 !important;
    border-radius: 10px !important;
    color: #3C3489 !important;
    font-size: 0.9rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #7F77DD !important;
    box-shadow: 0 0 0 3px #EEEDFE88 !important;
}
[data-testid="stTextInput"] input::placeholder { color: #AFA9EC !important; }

/* ── 件数セレクト（グリーン） ── */
[data-testid="stSelectbox"] > div > div {
    background: #E1F5EE !important;
    border: 1.5px solid #9FE1CB !important;
    border-radius: 10px !important;
    color: #085041 !important;
}

/* ── 検索・クロール実行ボタン（ティール） ── */
[data-testid="stButton"] > button {
    background: #1D9E75 !important; color: #fff !important;
    border: none !important; border-radius: 10px !important;
    font-size: 0.85rem !important; font-weight: 500 !important;
    padding: 10px 22px !important; transition: background 0.15s;
}
[data-testid="stButton"] > button:hover { background: #0F6E56 !important; }

/* ── テキストエリア（クローラータブ） ── */
[data-testid="stTextArea"] textarea {
    background: #EEEDFE !important;
    border: 1.5px solid #CECBF6 !important;
    border-radius: 10px !important;
    color: #3C3489 !important;
}

/* ── ページ全体の背景 ── */
.main { background: #fff; }
footer, #MainMenu { display: none; }
</style>
""", unsafe_allow_html=True)


# ── セッションステートの初期化 ────────────────────────────────
if "oyobidashi_flags" not in st.session_state:
    st.session_state["oyobidashi_flags"] = {}

# ── キャッシュ付きインデックス構築 ─────────────────────────────
@st.cache_resource
def load_and_index():
    """全ページを DB から読み込み TF-IDF インデックスを構築する。
    @st.cache_resource により、アプリ起動中は一度だけ実行される。"""
    pages = get_all_documents()
    if pages:
        rebuild_index(pages)
    return pages

pages = load_and_index()
engine = get_engine()

# ── ヘッダー ──────────────────────────────────────────────────
st.title("🔍 Tech0 Search v1.0")
st.caption("PROJECT ZERO — 社内ナレッジ検索エンジン【TF-IDFランキング搭載】")

with st.sidebar:
    st.header("DB の状態")
    st.metric("登録ページ数", f"{len(pages)} 件")
    if st.button("🔄 インデックスを更新"):
        st.cache_resource.clear()
        st.rerun()

# ── タブ ──────────────────────────────────────────────────────
tab_search, tab_crawl, tab_list, tab_post, tab_hot = st.tabs(
    ["🔍 検索", "🤖 クローラー", "📋 一覧", "💡 投稿", "🔥 Hot"]
)

# ── 検索タブ ───────────────────────────────────────────────────
with tab_search:
    st.subheader("キーワードで検索")

    col_search, col_options = st.columns([3, 1])
    with col_search:
        query = st.text_input("🔍 キーワードを入力", placeholder="例: DX, IoT, 製造業",
                              label_visibility="collapsed")
    with col_options:
        top_n = st.selectbox("表示件数", [10, 20, 50], index=0)

    if query:
        results = engine.search(query, top_n=top_n)

        st.markdown(f"**📊 検索結果：{len(results)} 件**（TF-IDFスコア順）")
        st.divider()

        if results:
            for i, page in enumerate(results, 1):
                with st.container():
                    col_rank, col_title, col_score = st.columns([0.5, 4, 1])
                    with col_rank:
                        # 上位3件にはメダルを表示する
                        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else str(i)
                        st.markdown(f"### {medal}")
                    with col_title:
                        st.markdown(f"### {page['title']}")
                    with col_score:
                        # relevance_score（最終スコア）と base_score（TF-IDFのみ）を両方表示
                        st.metric("スコア", f"{page['relevance_score']}",
                                  delta=f"基準: {page['base_score']}")

                    desc = page.get("description", "")
                    if desc:
                        st.markdown(f"*{desc[:200]}{'...' if len(desc) > 200 else ''}*")

                    kw = page.get("keywords", "") or ""
                    if kw:
                        kw_list = [k.strip() for k in kw.split(",") if k.strip()][:5]
                        tags = " ".join([f"`{k}`" for k in kw_list])
                        st.markdown(f"🏷️ {tags}")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.caption(f"👤 {page.get('author', '不明') or '不明'}")
                    with col2: st.caption(f"📊 {page.get('word_count', 0)} 語")
                    with col3: st.caption(f"📁 {page.get('category', '未分類') or '未分類'}")
                    with col4: st.caption(f"📅 {(page.get('crawled_at', '') or '')[:10]}")

                    st.markdown(f"🔗 [{page['url']}]({page['url']})")
                    st.divider()
        else:
            st.info("該当するページが見つかりませんでした")

# ── クローラータブ ─────────────────────────────────────────────
if "crawl_results" not in st.session_state:
    st.session_state.crawl_results = []

with tab_crawl:
    st.subheader("🤖 自動クローラー")
    st.caption("URLを入力してクロールし、インデックスに登録する")

    crawl_url_input = st.text_area(
        "クロール対象URL",
        placeholder="URLを改行またはスペース区切りで入力してください",
        height=150
    )

    if st.button("🤖 クロール実行", type="primary"):
        if crawl_url_input:
            raw_parts = re.split(r'[\s]+', crawl_url_input.strip())
            urls = [p for p in raw_parts if p.startswith(("http://", "https://"))]

            if not urls:
                st.error("有効なURLが見つかりませんでした")
            else:
                st.write(f"🔗 {len(urls)}件のURLを処理します")

                st.session_state.crawl_results = []

                for url in urls:
                    with st.spinner(f"クロール中: {url}"):
                        result = crawl_url(url)

                    if result and result.get('crawl_status') == 'success':
                        st.success(f"✅ 成功: {url}")

                        col1, col2 = st.columns(2)
                        with col1:
                            title = result.get('title', '')
                            st.metric("📄 タイトル", (title[:30] + "...") if len(title) > 30 else title)
                        with col2:
                            st.metric("📊 文字数", f"{result.get('word_count', 0)}語")

                        st.session_state.crawl_results.append(result)
                    else:
                        st.error(f"❌ 失敗: {url}")

    if st.session_state.crawl_results:
        st.info(f"{len(st.session_state.crawl_results)}件のクロール結果を登録できます。")

        if st.button("💾 全てインデックスに登録"):
            total = len(st.session_state.crawl_results)

            progress_text = st.empty()
            progress_bar = st.progress(0)

            for i, r in enumerate(st.session_state.crawl_results, start=1):
                progress_text.write(f"📥 {i} / {total} 件登録中...")
                insert_document(r)
                progress_bar.progress(i / total)

            progress_text.write(f"✅ {total} / {total} 件 登録完了！")
            st.success(f"{total}件 登録完了！")
            st.session_state.crawl_results = []
            st.cache_resource.clear()
            st.rerun()

# ── 一覧タブ ───────────────────────────────────────────────────
with tab_list:
    st.subheader(f"📋 登録済みページ一覧（{len(pages)} 件）")
    if not pages:
        st.info("登録されているページがありません。クローラータブからページを追加してください。")
    else:
        for page in pages:
            with st.expander(f"📄 {page['title']}"):
                st.markdown(f"**URL：** {page['url']}")
                st.markdown(f"**説明：** {page.get('description', '（なし）') or '（なし）'}")
                col1, col2, col3 = st.columns(3)
                with col1: st.caption(f"語数：{page.get('word_count', 0)}")
                with col2: st.caption(f"作成者：{page.get('author', '不明') or '不明'}")
                with col3: st.caption(f"カテゴリ：{page.get('category', '未分類') or '未分類'}")

with tab_post:

    # ── お呼び出し通知（フラグが立っていたら一番上に表示） ────
    for post_id, flagged in list(st.session_state["oyobidashi_flags"].items()):
        if not flagged:
            continue

        all_posts_for_flag = get_all_posts()
        target_post = None
        for p in all_posts_for_flag:
            if p["id"] == post_id:
                target_post = p
                break

        if target_post is None:
            continue

        with st.container(border=True):
            st.markdown("##### 📣 黒崎からのお呼び出し")
            st.caption("黒崎 厳　執行役員 / 経営企画担当")
            st.write("あなたの提案に注目しています。")
            st.write("詳しくお話を聞かせてください。")
            st.write("下記の日時に私の部屋までお越しください。")

            with st.container(border=True):
                st.write("🗓　12月5日（木）14:00")
                st.caption("黒崎執行役員室（本館5F）")

            with st.container(border=True):
                st.caption("対象スレッド")
                st.write(target_post["text"][:40] + "…")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("後で確認する", key=f"later_{post_id}"):
                    st.session_state["oyobidashi_flags"][post_id] = False
                    st.rerun()
            with col2:
                if st.button("承知しました ✓", key=f"accept_{post_id}"):
                    st.session_state["oyobidashi_flags"][post_id] = False
                    st.success("承知しました！当日お伺いします。")
                    st.rerun()

    st.divider()

    # ── 投稿フォーム ──────────────────────────────────────────
    with st.form("post_form", clear_on_submit=True):
        text   = st.text_area("投稿", placeholder="アイデアを書いてみよう")
        # デモではユーザー名を識別できないので、黒崎で統一する
        post_name = "黒崎 厳"
        anonymous = st.checkbox("匿名で投稿する")
        submitted = st.form_submit_button("投稿する")

        if submitted:
            if not text.strip():
                st.warning("投稿を入力してください")
            else:
                insert_post(text, post_name, anonymous)
                st.success("投稿しました")
                st.rerun()

    st.divider()

    # ── 投稿一覧 ──────────────────────────────────────────────
    # DBから全投稿を取得して表示する
    all_posts = get_all_posts()
    st.subheader(f"📋 投稿一覧（{len(all_posts)} 件）")

    if not all_posts:
        st.info("まだ投稿がありません。")
    else:
        for post in all_posts:
            # 匿名フラグが1（True）なら名前を隠す
            if post["anonymous"] == 1:
                display_name = "匿名"
            else:
                display_name = post["name"]

            st.markdown(f"**{display_name}**　{post['posted_at'][:10]}")
            st.markdown(f"> {post['text']}")

            # いいね数を取得して表示する
            like_count = get_like_count(post["id"])
            st.caption(f"⭐ いいね {like_count} 件")
            st.divider()

# ============================================================
# 🔥 Hotタブ
# ============================================================
with tab_hot:
    st.subheader("🔥 今話題の投稿")

    # いいね数の多い順に並び替えて上位10件を取得する
    hot_posts = get_hot_posts()

    if not hot_posts:
        st.info("投稿はありません。最初のアイデアを投稿してみましょう💡")
    else:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}

        for rank, post in enumerate(hot_posts, start=1):
            if post["anonymous"]:
                name = "匿名ユーザー"
            else:
                name = post["name"]

            medal = medals[rank] if rank in medals else f"#{rank}"

            with st.container(border=True):
                col_rank, col_body, col_like = st.columns([0.5, 5, 1])

                with col_rank:
                    st.markdown(f"### {medal}")

                with col_body:
                    # 先頭40文字をタイトル代わりにして、クリックで本文を展開する
                    preview = post["text"][:40] + "…" if len(post["text"]) > 40 else post["text"]
                    with st.expander(preview):
                        st.caption(f"{name}")
                        st.write(post["text"])

                with col_like:
                    like_count = get_like_count(post["id"])
                    st.metric("❤️", like_count)

                # いいねボタンが押された場合の挙動
                # key：どの投稿のいいねボタンかを特定する
                if st.button("👍 いいね", key=f"like_btn_{post['id']}"):
                    add_like(post["id"])
                    st.rerun()

                # お呼び出しボタン（閾値を超えた投稿にだけ表示）
                like_count = get_like_count(post["id"])
                already_sent = st.session_state["oyobidashi_flags"].get(post["id"], False)
                if like_count >= OYOBIDASHI_THRESHOLD:
                    if already_sent:
                        st.success("📣 お呼び出し済み")
                    else:
                        if st.button("📣 お呼び出しを送る", key=f"oyobidashi_btn_{post['id']}"):
                            st.session_state["oyobidashi_flags"][post["id"]] = True
                            st.toast("お呼び出しを送りました", icon="📣")
                            st.rerun()

st.divider()
st.caption("© 2025 PROJECT ZERO — Tech0 Search v1.0 | Powered by TF-IDF")

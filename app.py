"""
app.py — Tech0 Search v1.0（完成版）
Streamlit アプリ本体。検索・クローラー・一覧の3タブ構成。
"""

import re
import streamlit as st
from database import init_db, get_all_pages, insert_page, log_search
from ranking import get_engine, rebuild_index
from crawler import crawl_url

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




# ── キャッシュ付きインデックス構築 ─────────────────────────────
@st.cache_resource
def load_and_index():
    """全ページを DB から読み込み TF-IDF インデックスを構築する。
    @st.cache_resource により、アプリ起動中は一度だけ実行される。"""
    pages = get_all_pages()
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
tab_search, tab_crawl, tab_list = st.tabs(
    ["🔍 検索", "🤖 クローラー", "📋 一覧"]
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
        log_search(query, len(results))    # 検索するたびに自動記録（Step7で実装予定）

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
                insert_page(r)
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

st.divider()
st.caption("© 2025 PROJECT ZERO — Tech0 Search v1.0 | Powered by TF-IDF")

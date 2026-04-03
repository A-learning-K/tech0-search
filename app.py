"""
app.py — Tech0 Search v1.0（完成版）
Streamlit アプリ本体。検索・クローラー・一覧の3タブ構成。
"""

import re
import streamlit as st
from database import init_db, get_all_documents, insert_document, insert_post, get_all_posts, add_like, get_like_count, get_hot_posts
from ranking import get_engine, rebuild_index
from crawler import crawl_url
from streamlit_option_menu import option_menu


# ── 定数 ──────────────────────────────────────────────────────
OYOBIDASHI_THRESHOLD = 3  # お呼び出し閾値（デモ用に低め設定。本番は100）

# アプリ起動時に DB を初期化する（テーブルが未作成なら作る）
init_db()

st.set_page_config(
    page_title="TECHZERON SEARCH ポータル",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全体デザイン ───────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif;
}

/* ── ページ全体の背景 ── */
.main {
    background: #fdfaf6 !important;
    color: #2e2820 !important;
}

[data-testid="stAppViewContainer"] {
  background: #fdfaf6 !important;
  /* overflow: visible を削除 */
}
[data-testid="stMain"] {
  background: #fdfaf6 !important;
  /* overflow: visible を削除 */
}
                 
/* ── サイドバー ── */
[data-testid="stSidebar"] {
    background: #f0ebe2 !important;
    border-right: 1px solid #ddd6c8 !important;
}
[data-testid="stSidebar"] * { color: #3a3028 !important; }
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #2e2820 !important; font-size: 1.8rem !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    background: #c4a882 !important; color: #2e2820 !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
    background: #b09070 !important;
}


/* ── 検索入力 ── */
[data-testid="stTextInput"] input {
    background: #fff !important;
    border: 1px solid #ddd4c8 !important;
    border-radius: 10px !important;
    color: #2e2820 !important;
    font-size: 0.9rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #b09070 !important;
    box-shadow: 0 0 0 3px #f0ebe288 !important;
}
[data-testid="stTextInput"] input::placeholder { color: #b0a498 !important; }

/* ── セレクトボックス ── */
[data-testid="stSelectbox"] > div > div {
    background: #fff !important;
    border: 1px solid #ddd4c8 !important;
    border-radius: 10px !important;
    color: #2e2820 !important;
}

/* ── ボタン ── */
[data-testid="stButton"] > button {
    background: #E85D24 !important; color: #fff !important;
    border: none !important; border-radius: 10px !important;
    font-size: 0.85rem !important; font-weight: 500 !important;
    padding: 10px 22px !important; transition: background 0.15s;
}
[data-testid="stButton"] > button:hover {
    background: #c94d1a !important;
}
            
/* ── 投稿フォーム送信ボタン── */
[data-testid="stFormSubmitButton"] > button {
    background: #E85D24 !important; color: #fff !important;
    border: none !important; border-radius: 10px !important;
    font-size: 0.85rem !important; font-weight: 500 !important;
    padding: 10px 22px !important; transition: background 0.15s;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: #c94d1a !important;
}
            
/* ── ボタンテキストの文字色を白に固定 ── */
[data-testid="stButton"] > button p,
[data-testid="stButton"] > button span,
[data-testid="stButton"] > button div,
[data-testid="stFormSubmitButton"] > button p,
[data-testid="stFormSubmitButton"] > button span,
[data-testid="stFormSubmitButton"] > button div {
    color: #fff !important;
}
            

/* ── テキストエリア ── */
[data-testid="stTextArea"] textarea {
    background: #fff !important;
    border: 1px solid #ddd4c8 !important;
    border-radius: 10px !important;
    color: #2e2820 !important;
}

/* ── 全体テキスト ── */
p, span, label, div {
    color: #2e2820;
}

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
st.markdown("""
<div style="
  display:flex; align-items:center; gap:12px;
  padding:0 18px; height:52px;
  background:#f0ebe2; border-bottom:1px solid #ddd6c8;
  position:sticky; top:0; z-index:999;
  margin:-1rem -1rem 1rem -1rem;
">
  <div style="width:28px;height:28px;background:#E85D24;border-radius:4px;
    display:flex;align-items:center;justify-content:center;">
    <svg width="16" height="16" viewBox="0 0 16 16" fill="#fff">
      <path d="M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z"/>
    </svg>
  </div>
  <span style="font-size:13px;font-weight:500;color:#2e2820;">
    TECHZERON<b style="color:#E85D24;"> SEARCH</b> ポータル
  </span>
</div>
""", unsafe_allow_html=True)


# ── サイドバー ──────────────────────────────────────────────────────
with st.sidebar:
    selected = option_menu(
        menu_title=None,
        options=["🔍 検索", "💡 投稿", "🤖 クローラー", "一覧"],
        icons=["search", "chat-square-text", "database-add", "card-list"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#e3dccf"},
            "icon": {"color": "#826548", "font-size": "15px"},
            "nav-link": {
                "font-size": "14px",
                "font-weight": "bold",
                "text-align": "left",
                "margin": "2px 0px",
                "border-radius": "8px",
                "color": "#5a5048",
                "--hover-color": "#b0aba2",
            },
            "nav-link-selected": {
                "background-color": "#E85D24",
                "color": "#ffffff",
                "font-weight": "bold",
            },
        }
    )

 #------HOT欄---------
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


# ── 検索ページ ───────────────────────────────────────────────────
if selected == "🔍 検索":
    st.subheader("🔍 検索")
    st.write("社内情報を横断的に検索できます")

    col_search, col_options = st.columns([3, 1])
    with col_search:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
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

# ── 投稿ページ ─────────────────────────────────────────────
elif selected == "💡 投稿":
    st.subheader("💡 投稿")
    st.write("あなたのアイデアを全社に提案できます。")
    st.write("たくさんの「⭐いいね」を集めたアイデアは、経営会議で検討の対象となります")


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
        submitted = st.form_submit_button("投稿する",type="primary")

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


# ── クローラーページ ─────────────────────────────────────────────
if "crawl_results" not in st.session_state:
    st.session_state.crawl_results = []

elif selected == "🤖 クローラー":
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

# ── 一覧ページ ───────────────────────────────────────────────────
elif selected == "📋 一覧":
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

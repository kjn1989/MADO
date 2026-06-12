"""MADO — Meet AI, Discover Opportunities
Streamlit エントリポイント(第1段階)。

このファイルは「UIの配線」だけを行う薄い層です。
検索・生成・出典組立はすべて mado_core.ask() に委譲しており、
第2段階では FastAPI(api/main.py)が同じ ask() を呼びます。
"""
from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # ローカル実行時。Cloudでは st.secrets から下で補完

import mado_core
from mado_core.schemas import NOT_FOUND_MESSAGE
from ui import cards, chat, filters, header, styles, suggestions

# ---------------------------------------------------------------- 初期設定
st.set_page_config(
    page_title="MADO — Meet AI, Discover Opportunities",
    page_icon="assets/favicon.svg" if os.path.exists("assets/favicon.svg") else "🪟",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Streamlit Cloud では secrets を環境変数へ橋渡し(mado_core はenvだけを見る)
for k in ("GEMINI_API_KEY", "MADO_GEMINI_MODEL", "MADO_SIM_THRESHOLD"):
    try:
        if k in st.secrets and not os.getenv(k):
            os.environ[k] = str(st.secrets[k])
    except Exception:
        pass  # secrets.toml が無いローカル環境

styles.inject(st)
header.render(st)


# 埋め込みモデルはプロセス内で1回だけロード(初回のみ1〜2分かかる場合あり)
@st.cache_resource(show_spinner="多言語埋め込みモデルを準備しています(初回のみ1〜2分)…")
def _warmup():
    from mado_core.embeddings import embed
    embed(["warmup"])
    return True


# ---------------------------------------------------------------- サイドバー
countries, topics, lang_pref = filters.render(st)
catalog = filters.load_catalog()

# ---------------------------------------------------------------- 状態
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------- 初回ヒーロー
pending = None
if not st.session_state.messages:
    pending = suggestions.render(st, n_videos=len(catalog["videos"]))

# ---------------------------------------------------------------- 履歴再描画
chat.render_history(st, st.session_state.messages)

# ---------------------------------------------------------------- 入力
prompt = st.chat_input("JICAの動画アーカイブに質問する / Ask the JICA video archive")
question = prompt or pending

if question:
    if not os.getenv("GEMINI_API_KEY"):
        st.error(
            "GEMINI_API_KEY が設定されていません。"
            "ローカルでは `.env`、Streamlit Cloud では Settings → Secrets に設定してください。"
        )
        st.stop()

    _warmup()

    st.session_state.messages.append({"role": "user", "content": question, "result": None})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🪟"):
        with st.spinner("アーカイブの窓を開けています…"):
            result, stream = mado_core.ask(
                question, countries=countries or None, topics=topics or None, lang=lang_pref
            )

        if not result.found:
            text = NOT_FOUND_MESSAGE[result.language]
            st.markdown(text)
        else:
            try:
                text = st.write_stream(stream)  # 回答ストリーミング表示
            except Exception as e:
                text = (
                    "回答の生成中にエラーが発生しました。少し時間をおいて再度お試しください。"
                    f"\n\n`{e}`"
                )
                st.markdown(text)
            for n in result.notices:
                st.caption(f"ℹ️ {n}")
            cards.render_sources(st, result.sources, result.language)
            cards.render_related(st, result.related, result.language)

    st.session_state.messages.append(
        {"role": "assistant", "content": text if isinstance(text, str) else "", "result": result}
    )
    if pending:  # 質問例ボタン経由のときはヒーローを消すため再描画
        st.rerun()

# ---------------------------------------------------------------- フッター
header.render_footer(st)

"""チャット履歴の再描画ヘルパー。

session_state.messages の各要素:
  {"role": "user"|"assistant", "content": str,
   "result": AnswerResult | None}   # assistant のみ
"""
from ui import cards


def render_history(st, messages: list[dict]):
    for msg in messages:
        avatar = "🪟" if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            result = msg.get("result")
            if result and result.found:
                for n in result.notices:
                    st.caption(f"ℹ️ {n}")
                cards.render_sources(st, result.sources, result.language)
                cards.render_related(st, result.related, result.language)

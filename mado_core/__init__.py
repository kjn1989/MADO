"""MADO core — UI非依存のRAGエンジン。

唯一の公開API:
    result, stream = mado_core.ask(question, countries=..., topics=..., lang="auto")

- result: AnswerResult(found / sources / related / notices)。JSON化可能。
- stream: 回答テキストの Iterator[str](found=False のとき None)。

第1段階: Streamlit(app.py)がこれを呼ぶ。
第2段階: FastAPI(api/main.py)が同じものを呼んでSSEに変換するだけ。
"""
from __future__ import annotations

from typing import Iterator, Optional

from .config import get_settings
from .generator import detect_language, stream_answer
from .related import find_related
from .retriever import retrieve
from .schemas import AnswerResult, SourceVideo, NOT_FOUND_MESSAGE

__all__ = ["ask", "AnswerResult", "NOT_FOUND_MESSAGE", "get_settings"]

NOTICE = {
    "ja": "一部の根拠は字幕のない動画のため、タイトル・説明文のみに基づいています。",
    "en": "Some sources have no captions; those parts are based on titles/descriptions only.",
}


def ask(
    question: str,
    countries: Optional[list[str]] = None,
    topics: Optional[list[str]] = None,
    lang: str = "auto",
) -> tuple[AnswerResult, Optional[Iterator[str]]]:
    if lang == "auto":
        lang = detect_language(question)

    chunks, q_emb = retrieve(question, countries, topics)

    # ハルシネーション防止: 根拠チャンクが無ければ生成しない
    if not chunks:
        return AnswerResult(found=False, language=lang), None

    # --- 出典カード(LLMを介さず機械的に組み立て = 出典捏造の余地なし) ---
    s = get_settings()
    sources: list[SourceVideo] = []
    seen: set[str] = set()
    for h in chunks:
        m = h["meta"]
        if m["video_id"] in seen:
            continue
        seen.add(m["video_id"])
        meta_only = m.get("source_type") == "metadata_only"
        sources.append(
            SourceVideo(
                video_id=m["video_id"],
                title=m.get("title", ""),
                channel=m.get("channel", ""),
                published_at=m.get("published_at", ""),
                thumbnail=m.get(
                    "thumbnail", f"https://i.ytimg.com/vi/{m['video_id']}/mqdefault.jpg"
                ),
                start_sec=None if meta_only else int(m.get("start_sec") or 0),
                snippet=(h["text"][:90] + "…") if len(h["text"]) > 90 else h["text"],
                captions_based=not meta_only,
            )
        )
        if len(sources) >= s.max_source_videos:
            break

    notices = []
    if any(not s_.captions_based for s_ in sources):
        notices.append(NOTICE[lang])

    related = find_related(
        q_emb, {s_.video_id for s_ in sources}, [h["meta"] for h in chunks], lang
    )

    result = AnswerResult(
        found=True, language=lang, sources=sources, related=related, notices=notices
    )
    return result, stream_answer(question, chunks, lang)

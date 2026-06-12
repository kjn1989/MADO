"""関連動画の選定。

回答に使った動画の「近傍テーマ」をベクトル空間で探し、根拠動画と重複しない
2〜4本を返す。関連理由は共有タグからテンプレートで生成(無料・決定的・捏造ゼロ)。
"""
from __future__ import annotations

from .config import get_settings
from .schemas import RelatedVideo

REASON_T = {
    "ja": {
        "topic":   "同じ「{tag}」分野を扱う動画です",
        "country": "同じ{tag}に関する動画です",
        "channel": "同チャンネル({ch})の近いテーマの動画です",
        "default": "質問内容と近いテーマの動画です",
    },
    "en": {
        "topic":   'Covers the same topic: "{tag}"',
        "country": "Also about {tag}",
        "channel": "A closely related video on the same channel ({ch})",
        "default": "Thematically close to your question",
    },
}


def _tags(meta: dict, key: str) -> set[str]:
    return {t.strip() for t in (meta.get(key) or "").split(",") if t.strip()}


def _reason(meta: dict, src_metas: list[dict], lang: str) -> str:
    t = REASON_T[lang]
    src_topics = set().union(*[_tags(m, "topics") for m in src_metas]) if src_metas else set()
    src_countries = set().union(*[_tags(m, "countries") for m in src_metas]) if src_metas else set()
    shared_topic = _tags(meta, "topics") & src_topics
    if shared_topic:
        return t["topic"].format(tag=sorted(shared_topic)[0])
    shared_country = _tags(meta, "countries") & src_countries
    if shared_country:
        return t["country"].format(tag=sorted(shared_country)[0])
    src_channels = {m.get("channel") for m in src_metas}
    if meta.get("channel") in src_channels:
        return t["channel"].format(ch=meta.get("channel"))
    return t["default"]


def find_related(
    q_emb: list[float], source_video_ids: set[str], src_metas: list[dict], lang: str
) -> list[RelatedVideo]:
    from . import vectorstore

    s = get_settings()
    try:
        hits = vectorstore.query(q_emb, s.top_k * 2)
    except Exception:
        return []

    seen: set[str] = set(source_video_ids)
    out: list[RelatedVideo] = []
    for h in hits:
        m = h["meta"]
        vid = m["video_id"]
        if vid in seen:
            continue
        seen.add(vid)
        out.append(
            RelatedVideo(
                video_id=vid,
                title=m.get("title", ""),
                channel=m.get("channel", ""),
                thumbnail=m.get("thumbnail", f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"),
                reason=_reason(m, src_metas, lang),
            )
        )
        if len(out) >= s.related_count:
            break
    return out

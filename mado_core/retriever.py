"""Retriever: 検索 → メタデータ絞り込み → 再ランキング → 閾値判定。

ハルシネーション防止の第一関門:
similarity_threshold を超えるチャンクが1つも無ければ found=False を返し、
生成(LLM呼び出し)は一切行わない。
"""
from __future__ import annotations

from .config import get_settings
from .embeddings import embed


def _match_tags(meta: dict, key: str, selected: list[str] | None) -> bool:
    """countries / topics はカンマ区切り文字列としてメタデータに格納。
    Chroma の where はスカラー比較のみのため、タグ絞り込みは Python 側で行う。"""
    if not selected:
        return True
    tags = {t.strip() for t in (meta.get(key) or "").split(",") if t.strip()}
    return bool(tags & set(selected))


def _rerank_score(hit: dict) -> float:
    """類似度を主、軽い補正を従とした再ランキング。
    - 公式字幕由来チャンクをわずかに優遇(自動字幕の誤認識リスクを相対的に下げる)
    - metadata_only(字幕なし)チャンクはわずかに減点
    """
    s = hit["similarity"]
    src = hit["meta"].get("source_type", "caption")
    if src == "manual_caption":
        s += 0.02
    elif src == "metadata_only":
        s -= 0.03
    return s


def retrieve(
    question: str,
    countries: list[str] | None = None,
    topics: list[str] | None = None,
):
    """return (chunks, query_embedding). chunks は再ランク済み・閾値通過分のみ。"""
    s = get_settings()
    q_emb = embed([question])[0]

    hits = _query_safe(q_emb, s.top_k)

    # メタデータ絞り込み(国・分野)
    hits = [
        h for h in hits
        if _match_tags(h["meta"], "countries", countries)
        and _match_tags(h["meta"], "topics", topics)
    ]

    # 閾値判定 → 再ランキング
    hits = [h for h in hits if h["similarity"] >= s.similarity_threshold]
    hits.sort(key=_rerank_score, reverse=True)

    # 動画ごとに最大2チャンクまで(根拠の多様性確保)、全体で max_context_chunks
    per_video: dict[str, int] = {}
    selected = []
    for h in hits:
        vid = h["meta"]["video_id"]
        if per_video.get(vid, 0) >= 2:
            continue
        per_video[vid] = per_video.get(vid, 0) + 1
        selected.append(h)
        if len(selected) >= s.max_context_chunks:
            break

    return selected, q_emb


def _query_safe(q_emb, n):
    from . import vectorstore
    try:
        return vectorstore.query(q_emb, n)
    except Exception:
        # 索引が空 / 未構築の場合
        return []

"""多言語埋め込み(MiniLM)。ローカル実行・無料。
日本語の質問 ←→ 英語字幕チャンクのクロスリンガル検索を担う。
モデルはプロセス内シングルトン(Streamlit側では @st.cache_resource でさらにキャッシュ)。
"""
from __future__ import annotations

from functools import lru_cache

from .config import get_settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(get_settings().embed_model, device="cpu")


def embed(texts: list[str]) -> list[list[float]]:
    vecs = _model().encode(
        texts, normalize_embeddings=True, show_progress_bar=False, batch_size=32
    )
    return [v.tolist() for v in vecs]

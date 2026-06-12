"""MADO core settings.

すべて環境変数で差し替え可能。Streamlit / FastAPI のどちらからも
同じ get_settings() を呼ぶだけで動く(UI非依存)。
"""
from __future__ import annotations

import os
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class Settings:
    # --- API keys ---
    gemini_api_key: str
    # --- models (差し替えポイント) ---
    gemini_model: str
    embed_model: str
    # --- storage ---
    chroma_dir: str
    catalog_path: str
    collection: str
    # --- retrieval ---
    top_k: int                  # ベクトル検索で取得するチャンク数(フィルタ前)
    max_source_videos: int      # 回答の根拠として使う動画数の上限
    max_context_chunks: int     # LLMに渡すチャンク数の上限
    similarity_threshold: float # これ未満なら「該当動画なし」(ハルシネーション防止)
    related_count: int          # 関連動画の提示数(2〜4)


def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("MADO_GEMINI_MODEL", "gemini-2.0-flash"),
        embed_model=os.getenv(
            "MADO_EMBED_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        ),
        chroma_dir=os.getenv("MADO_CHROMA_DIR", os.path.join(ROOT, "data", "chroma")),
        catalog_path=os.getenv(
            "MADO_CATALOG", os.path.join(ROOT, "data", "catalog.json")
        ),
        collection=os.getenv("MADO_COLLECTION", "mado_chunks"),
        top_k=int(os.getenv("MADO_TOP_K", "40")),
        max_source_videos=int(os.getenv("MADO_MAX_SOURCES", "3")),
        max_context_chunks=int(os.getenv("MADO_MAX_CONTEXT", "8")),
        similarity_threshold=float(os.getenv("MADO_SIM_THRESHOLD", "0.35")),
        related_count=int(os.getenv("MADO_RELATED", "4")),
    )

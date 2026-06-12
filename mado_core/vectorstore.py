"""ChromaDB 抽象化レイヤー。

第2段階で pgvector へ移行する場合は、このファイルの
get_collection() / query() / upsert() を差し替えるだけでよい。
"""
from __future__ import annotations

from functools import lru_cache

from .config import get_settings


@lru_cache(maxsize=1)
def _client():
    import chromadb
    return chromadb.PersistentClient(path=get_settings().chroma_dir)


def get_collection():
    s = get_settings()
    return _client().get_or_create_collection(
        s.collection, metadata={"hnsw:space": "cosine"}
    )


def query(embedding: list[float], n: int) -> list[dict]:
    """類似チャンクを取得し {text, meta, similarity} のリストで返す。"""
    col = get_collection()
    res = col.query(
        query_embeddings=[embedding],
        n_results=min(n, max(col.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )
    out = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        out.append({"text": doc, "meta": meta, "similarity": 1.0 - float(dist)})
    return out


def upsert(ids, embeddings, documents, metadatas):
    get_collection().upsert(
        ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
    )

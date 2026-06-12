"""Step 5: チャンクを埋め込み ChromaDB に格納 + フィルタ用カタログ生成

出力:
- data/chroma/        (ベクトル索引・リポジトリにコミットしてCloudへ持っていく)
- data/catalog.json   (動画一覧+タグ。フィルタUIと統計表示に使用)
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mado_core.embeddings import embed          # noqa: E402
from mado_core import vectorstore               # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
BATCH = 64


def main():
    with open(os.path.join(RAW, "chunks.json"), encoding="utf-8") as f:
        chunks = json.load(f)
    tags = {}
    tags_path = os.path.join(RAW, "tags.json")
    if os.path.exists(tags_path):
        with open(tags_path, encoding="utf-8") as f:
            tags = json.load(f)

    col = vectorstore.get_collection()
    existing = set()
    try:
        existing = set(col.get(include=[])["ids"])
    except Exception:
        pass
    todo = [c for c in chunks if c["chunk_id"] not in existing]
    print(f"索引対象 {len(todo)} チャンク(既存 {len(existing)} はスキップ)")

    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        embs = embed([c["text"] for c in batch])
        metas = []
        for c in batch:
            t = tags.get(c["video_id"], {"countries": [], "topics": []})
            metas.append({
                "video_id": c["video_id"], "title": c["title"], "channel": c["channel"],
                "published_at": c["published_at"], "thumbnail": c["thumbnail"],
                "start_sec": c["start_sec"] if c["start_sec"] is not None else -1,
                "lang": c["lang"], "source_type": c["source_type"],
                "countries": ",".join(t["countries"]), "topics": ",".join(t["topics"]),
            })
        vectorstore.upsert(
            ids=[c["chunk_id"] for c in batch],
            embeddings=embs,
            documents=[c["text"] for c in batch],
            metadatas=metas,
        )
        print(f"  {min(i + BATCH, len(todo))}/{len(todo)}")

    # --- フィルタUI用カタログ ---
    videos: dict[str, dict] = {}
    for c in chunks:
        vid = c["video_id"]
        if vid not in videos:
            t = tags.get(vid, {"countries": [], "topics": []})
            videos[vid] = {
                "video_id": vid, "title": c["title"], "channel": c["channel"],
                "published_at": c["published_at"], "thumbnail": c["thumbnail"],
                "has_captions": c["source_type"] != "metadata_only",
                "countries": t["countries"], "topics": t["topics"],
            }
        elif c["source_type"] != "metadata_only":
            videos[vid]["has_captions"] = True

    catalog = {
        "videos": sorted(videos.values(), key=lambda v: v["published_at"], reverse=True),
        "countries": sorted({c for v in videos.values() for c in v["countries"]}),
        "topics": sorted({t for v in videos.values() for t in v["topics"]}),
        "channels": sorted({v["channel"] for v in videos.values()}),
    }
    cat_path = os.path.join(ROOT, "data", "catalog.json")
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False)
    print(f"カタログ {len(videos)} 動画 → {cat_path}")
    print(f"索引完了。コレクション件数: {col.count()}")


if __name__ == "__main__":
    main()

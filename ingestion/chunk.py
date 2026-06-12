"""Step 3: 字幕を 60〜90秒・時刻情報つきチャンクに分割 → data/raw/chunks.json

- 字幕あり: セグメントを連結し、75秒到達 or 文字数上限で区切る(目安60〜90秒)
- 字幕なし: タイトル+説明文を1チャンク(source_type=metadata_only)として索引
  → 検索ヒットは可能だが、UI/回答で「字幕なし」を明示する
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

TARGET_SEC = 75       # チャンク目標長(60〜90秒の中央)
MAX_CHARS = 1200      # 1チャンクの文字数上限(埋め込みモデルの実効長に配慮)
MIN_CHARS = 40        # これ未満の断片は前チャンクに併合


def chunk_segments(segments: list[dict]) -> list[dict]:
    chunks, buf, start = [], [], None
    for seg in segments:
        text = (seg.get("text") or "").replace("\n", " ").strip()
        if not text:
            continue
        if start is None:
            start = float(seg["start"])
        buf.append(text)
        end = float(seg["start"]) + float(seg.get("duration") or 0)
        joined = " ".join(buf)
        if (end - start) >= TARGET_SEC or len(joined) >= MAX_CHARS:
            chunks.append({"start_sec": int(start), "end_sec": int(end), "text": joined})
            buf, start = [], None
    if buf:
        tail = " ".join(buf)
        if chunks and len(tail) < MIN_CHARS:
            chunks[-1]["text"] += " " + tail
        else:
            chunks.append({
                "start_sec": int(start or 0),
                "end_sec": int(start or 0) + TARGET_SEC,
                "text": tail,
            })
    return chunks


def main():
    with open(os.path.join(RAW, "videos.json"), encoding="utf-8") as f:
        videos = json.load(f)

    all_chunks = []
    n_caption = n_meta = 0
    for v in videos:
        cap_path = os.path.join(RAW, "captions", f"{v['video_id']}.json")
        cap = None
        if os.path.exists(cap_path):
            with open(cap_path, encoding="utf-8") as f:
                cap = json.load(f)

        base = {
            "video_id": v["video_id"], "title": v["title"], "channel": v["channel"],
            "published_at": v["published_at"], "thumbnail": v["thumbnail"],
        }
        if cap and cap.get("segments"):
            for i, c in enumerate(chunk_segments(cap["segments"])):
                all_chunks.append({
                    **base, **c,
                    "chunk_id": f"{v['video_id']}-{i:04d}",
                    "lang": cap["lang"],
                    "source_type": cap["source_type"],  # manual_caption / auto_caption
                })
            n_caption += 1
        else:
            text = f"{v['title']}\n{(v.get('description') or '')[:1500]}".strip()
            all_chunks.append({
                **base,
                "chunk_id": f"{v['video_id']}-meta",
                "start_sec": None, "end_sec": None,
                "text": text,
                "lang": v.get("lang_hint", "ja"),
                "source_type": "metadata_only",
            })
            n_meta += 1

    out = os.path.join(RAW, "chunks.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False)
    print(f"チャンク {len(all_chunks)} 件 (字幕あり動画{n_caption} / 字幕なし動画{n_meta}) → {out}")


if __name__ == "__main__":
    main()

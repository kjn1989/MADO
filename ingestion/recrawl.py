"""差分クロール: 新規公開動画のみ 収集→字幕→チャンク→タグ→索引 を回す。

cron 例(毎日午前4時):
  0 4 * * * cd /path/to/mado && .venv/bin/python ingestion/recrawl.py >> recrawl.log 2>&1
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fetch_videos, fetch_captions, chunk, tag_videos, embed_index  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")


def main():
    old_ids = set()
    vpath = os.path.join(RAW, "videos.json")
    if os.path.exists(vpath):
        with open(vpath, encoding="utf-8") as f:
            old_ids = {v["video_id"] for v in json.load(f)}

    print("=== 1/5 メタデータ再取得(全件・低コスト) ===")
    fetch_videos.main()
    with open(vpath, encoding="utf-8") as f:
        new_count = len([v for v in json.load(f) if v["video_id"] not in old_ids])
    print(f"新規動画: {new_count} 本")
    if new_count == 0:
        print("新規なし。終了。")
        return

    print("=== 2/5 字幕(新規分のみ自動スキップ取得) ===")
    fetch_captions.main()
    print("=== 3/5 チャンク化 ===")
    chunk.main()
    print("=== 4/5 タグ付け(新規分のみ) ===")
    tag_videos.main()
    print("=== 5/5 索引(新規チャンクのみ) ===")
    embed_index.main()


if __name__ == "__main__":
    main()

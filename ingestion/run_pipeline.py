"""パイプライン一括実行。

プロトタイプ(2ch × 各20本):
  python ingestion/run_pipeline.py --channel-limit 2 --videos-per-channel 20
全件(8ch 全動画):
  python ingestion/run_pipeline.py
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fetch_videos, fetch_captions, chunk, tag_videos, embed_index  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--channel-limit", type=int, default=None)
    p.add_argument("--videos-per-channel", type=int, default=None)
    p.add_argument("--skip-tags", action="store_true", help="タグ付けを省略(最速で動かす場合)")
    a = p.parse_args()

    print("=== 1/5 動画メタデータ収集 ===")
    fetch_videos.main(a.channel_limit, a.videos_per_channel)
    print("\n=== 2/5 字幕取得 ===")
    fetch_captions.main()
    print("\n=== 3/5 チャンク分割 ===")
    chunk.main()
    if a.skip_tags:
        print("\n=== 4/5 タグ付け: スキップ ===")
    else:
        print("\n=== 4/5 国・分野タグ付け ===")
        tag_videos.main()
    print("\n=== 5/5 埋め込み・索引 ===")
    embed_index.main()
    print("\n✅ 完了。`streamlit run app.py` で起動できます。")

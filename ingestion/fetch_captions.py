"""Step 2: 字幕取得 → data/raw/captions/{video_id}.json

優先順位: 公式(手動)字幕 ja/en → 自動生成字幕 ja/en → 他言語の手動字幕。
youtube-transcript-api を使用(YouTube Data API のクォータを消費しない)。
再実行可能(取得済みはスキップ)。
"""
from __future__ import annotations

import json
import os
import time

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, NoTranscriptFound, VideoUnavailable,
)


def _list_transcripts(video_id: str):
    """youtube-transcript-api v0.6 / v1.x のAPI差を吸収。"""
    if hasattr(YouTubeTranscriptApi, "list_transcripts"):   # v0.6.x
        return YouTubeTranscriptApi.list_transcripts(video_id)
    return YouTubeTranscriptApi().list(video_id)            # v1.x

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
CAP_DIR = os.path.join(RAW, "captions")
PREFERRED = ["ja", "en"]


def _to_raw(fetched) -> list[dict]:
    """youtube-transcript-api の新旧バージョン差を吸収して dict のリストに正規化。"""
    if hasattr(fetched, "to_raw_data"):
        return fetched.to_raw_data()
    return [
        s if isinstance(s, dict)
        else {"text": s.text, "start": s.start, "duration": s.duration}
        for s in fetched
    ]


def fetch_one(video_id: str) -> dict | None:
    """return {"lang", "source_type", "segments":[{"start","duration","text"}]} or None"""
    tl = _list_transcripts(video_id)
    # 1) 公式(手動)字幕
    for lang in PREFERRED:
        try:
            t = tl.find_manually_created_transcript([lang])
            return {"lang": lang, "source_type": "manual_caption",
                    "segments": _to_raw(t.fetch())}
        except NoTranscriptFound:
            pass
    # 2) 自動生成字幕
    for lang in PREFERRED:
        try:
            t = tl.find_generated_transcript([lang])
            return {"lang": lang, "source_type": "auto_caption",
                    "segments": _to_raw(t.fetch())}
        except NoTranscriptFound:
            pass
    # 3) その他言語の手動字幕(最初の1つ)
    for t in tl:
        if not t.is_generated:
            return {"lang": t.language_code, "source_type": "manual_caption",
                    "segments": _to_raw(t.fetch())}
    return None


def main():
    os.makedirs(CAP_DIR, exist_ok=True)
    with open(os.path.join(RAW, "videos.json"), encoding="utf-8") as f:
        videos = json.load(f)

    ok = skip = none = 0
    for i, v in enumerate(videos, 1):
        vid = v["video_id"]
        path = os.path.join(CAP_DIR, f"{vid}.json")
        if os.path.exists(path):
            skip += 1
            continue
        try:
            cap = fetch_one(vid)
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
            cap = None
        except Exception as e:
            print(f"  [{vid}] error: {e} → 10秒待機して継続")
            time.sleep(10)
            cap = None
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cap, f, ensure_ascii=False)
        ok += cap is not None
        none += cap is None
        if i % 25 == 0:
            print(f"  {i}/{len(videos)} 処理済 (字幕あり{ok} / なし{none} / 既存{skip})")
        time.sleep(0.5)  # 礼儀的なレート制御

    print(f"完了: 字幕あり{ok} / なし{none} / スキップ{skip}")


if __name__ == "__main__":
    main()

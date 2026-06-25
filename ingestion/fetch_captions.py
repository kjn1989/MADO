"""Step 2: 字幕取得 → data/raw/captions/{video_id}.json

優先順位: 公式(手動)字幕 ja/en → 自動生成字幕 ja/en → 他言語の手動字幕。
youtube-transcript-api を使用(YouTube Data API のクォータを消費しない)。
再実行可能(取得済みはスキップ)。

全件(3,306本)取得時の注意:
  youtube-transcript-api は短時間に大量アクセスすると YouTube 側に
  IPレート制限(429 / TooManyRequests / IpBlocked 等)をかけられる。
  これは「時間をおけば回復する一時的エラー」であり、字幕が無いわけではない。
  そのため一時的エラーは指数バックオフで再試行し、それでも解消しない動画は
  結果ファイルを書かずにスキップする(= 次回実行で自動的に再取得を試みる)。
  確定的に字幕が無い動画(TranscriptsDisabled / 字幕未提供など)のみ null を
  キャッシュして再取得を省く。これにより一時的な失敗が「字幕なし」として
  恒久的に焼き付くことを防ぐ。
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

# 「確定的に字幕なし」= null をキャッシュしてよいエラー
DEFINITIVE_ERRORS = (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable)
MAX_RETRIES = 4       # 一時的エラー(レート制限・ネットワーク断)の再試行回数
BACKOFF_BASE = 5      # 指数バックオフ基準秒(5,10,20,40)


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


def fetch_captions_for(video_id: str) -> tuple[dict | None, str]:
    """字幕を取得し (結果, ステータス) を返す。

    ステータス:
      "ok"        … 字幕あり(dict)。ファイルに保存する。
      "none"      … 確定的に字幕なし。null をキャッシュして再取得を省く。
      "transient" … レート制限等の一時的エラーが再試行でも解消せず。
                    ファイルを書かず、次回実行で再取得を試みる。
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            cap = fetch_one(video_id)
            return cap, ("ok" if cap else "none")
        except DEFINITIVE_ERRORS:
            return None, "none"
        except Exception as e:
            # 確定的エラー以外はすべて「時間をおけば回復しうる一時的エラー」とみなす。
            # ここで null を書くと一時的失敗が「字幕なし」として焼き付くため書かない。
            if attempt >= MAX_RETRIES:
                print(f"  [{video_id}] 一時的エラーが解消せず: {e} → 今回はスキップ(次回再取得)")
                return None, "transient"
            wait = BACKOFF_BASE * (2 ** attempt)
            print(f"  [{video_id}] 一時的エラー: {e} → {wait}秒待機して再試行 ({attempt + 1}/{MAX_RETRIES})")
            time.sleep(wait)


def main():
    os.makedirs(CAP_DIR, exist_ok=True)
    with open(os.path.join(RAW, "videos.json"), encoding="utf-8") as f:
        videos = json.load(f)

    ok = skip = none = transient = 0
    for i, v in enumerate(videos, 1):
        vid = v["video_id"]
        path = os.path.join(CAP_DIR, f"{vid}.json")
        if os.path.exists(path):
            skip += 1
            continue
        cap, status = fetch_captions_for(vid)
        if status == "transient":
            transient += 1
            continue  # ファイルを書かない = 次回実行で自動的に再取得
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cap, f, ensure_ascii=False)
        ok += status == "ok"
        none += status == "none"
        if i % 25 == 0:
            print(f"  {i}/{len(videos)} 処理済 "
                  f"(字幕あり{ok} / なし{none} / 一時失敗{transient} / 既存{skip})")
        time.sleep(0.5)  # 礼儀的なレート制御

    print(f"完了: 字幕あり{ok} / なし{none} / 一時失敗(未取得){transient} / スキップ{skip}")
    if transient:
        print(f"⚠ {transient} 本は一時的エラー(レート制限等)で未取得です。"
              f"数分〜数十分おいて `python ingestion/fetch_captions.py` を再実行すると、"
              f"未取得分だけ自動的に取得を試みます。")


if __name__ == "__main__":
    main()

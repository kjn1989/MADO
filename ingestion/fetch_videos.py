"""Step 1: 8チャンネルの全動画メタデータを取得 → data/raw/videos.json

クォータ設計(1日10,000ユニット):
- channels.list (forHandle / id) : 1ユニット × 8 = 8
- playlistItems.list (50本/回, 1ユニット) : 全動画でも数十〜百ユニット程度
- search.list (100ユニット) はハンドル解決の最終フォールバックのみで使用
→ 8チャンネル全動画でも初回 ~200 ユニット以内で収まる想定。
"""
from __future__ import annotations

import json
import os
import sys
import time

import yaml
from dotenv import load_dotenv
from googleapiclient.discovery import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
CHANNELS_YAML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "channels.yaml")


def yt():
    load_dotenv(os.path.join(ROOT, ".env"))
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        sys.exit("YOUTUBE_API_KEY が未設定です(.env を確認)")
    return build("youtube", "v3", developerKey=key, cache_discovery=False)


def resolve_channel(api, ch: dict) -> dict | None:
    """handle / channel_id からチャンネル情報(uploads playlist含む)を解決。"""
    params = {"part": "contentDetails,snippet,statistics"}
    if ch.get("channel_id"):
        params["id"] = ch["channel_id"]
    else:
        params["forHandle"] = "@" + ch["handle"]
    res = api.channels().list(**params).execute()
    items = res.get("items", [])
    if not items and ch.get("handle"):
        # 旧 /c/ カスタムURL等で forHandle が解決できない場合の最終手段(100ユニット)
        print(f"  forHandle失敗 → search.list でフォールバック: {ch['name']}")
        sr = api.search().list(
            part="snippet", q=ch["name"], type="channel", maxResults=1
        ).execute()
        if sr.get("items"):
            cid = sr["items"][0]["snippet"]["channelId"]
            res = api.channels().list(part="contentDetails,snippet,statistics", id=cid).execute()
            items = res.get("items", [])
    if not items:
        print(f"  !! チャンネル解決失敗: {ch['name']}")
        return None
    it = items[0]
    return {
        "channel_id": it["id"],
        "name": ch["name"],
        "lang_hint": ch.get("lang_hint", "ja"),
        "uploads_playlist": it["contentDetails"]["relatedPlaylists"]["uploads"],
        "video_count": int(it.get("statistics", {}).get("videoCount", 0)),
    }


def fetch_playlist_videos(api, ch: dict, limit: int | None = None) -> list[dict]:
    videos, page_token = [], None
    while True:
        res = api.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=ch["uploads_playlist"],
            maxResults=50,
            pageToken=page_token,
        ).execute()
        for it in res.get("items", []):
            sn = it["snippet"]
            vid = it["contentDetails"]["videoId"]
            thumbs = sn.get("thumbnails", {})
            thumb = (thumbs.get("medium") or thumbs.get("default") or {}).get(
                "url", f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg"
            )
            videos.append({
                "video_id": vid,
                "title": sn.get("title", ""),
                "description": sn.get("description", ""),
                "published_at": it["contentDetails"].get(
                    "videoPublishedAt", sn.get("publishedAt", "")
                ),
                "thumbnail": thumb,
                "channel": ch["name"],
                "channel_id": ch["channel_id"],
                "lang_hint": ch["lang_hint"],
            })
            if limit and len(videos) >= limit:
                return videos
        page_token = res.get("nextPageToken")
        if not page_token:
            return videos


def main(channel_limit: int | None = None, videos_per_channel: int | None = None):
    os.makedirs(RAW, exist_ok=True)
    api = yt()
    with open(CHANNELS_YAML, encoding="utf-8") as f:
        channels = yaml.safe_load(f)["channels"]
    if channel_limit:
        channels = channels[:channel_limit]

    all_videos = []
    for ch in channels:
        print(f"[channel] {ch['name']}")
        info = resolve_channel(api, ch)
        if not info:
            continue
        vids = fetch_playlist_videos(api, info, videos_per_channel)
        print(f"  → {len(vids)} 本取得")
        all_videos.extend(vids)
        time.sleep(0.3)

    out = os.path.join(RAW, "videos.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=1)
    print(f"\n合計 {len(all_videos)} 本 → {out}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--channel-limit", type=int, default=None, help="先頭Nチャンネルのみ(プロトタイプ用)")
    p.add_argument("--videos-per-channel", type=int, default=None, help="各チャンネルN本のみ(プロトタイプ用)")
    a = p.parse_args()
    main(a.channel_limit, a.videos_per_channel)

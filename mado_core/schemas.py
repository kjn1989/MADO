"""MADO core schemas.

すべて dataclass + to_dict() で JSON 化可能。
第2段階(FastAPI + JSウィジェット)ではこのままAPIレスポンスになる。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


def _ts_url(video_id: str, start_sec: Optional[int]) -> str:
    base = f"https://www.youtube.com/watch?v={video_id}"
    if start_sec and start_sec > 0:
        return f"{base}&t={int(start_sec)}s"
    return base


@dataclass
class SourceVideo:
    """回答の根拠となった動画(タイムスタンプ付き)"""
    video_id: str
    title: str
    channel: str
    published_at: str
    thumbnail: str
    start_sec: Optional[int]          # 根拠チャンクの開始秒(字幕なしならNone)
    snippet: str                      # 根拠チャンクの冒頭(UI表示用・短く)
    captions_based: bool              # False = タイトル・説明文のみが根拠

    @property
    def url(self) -> str:
        return _ts_url(self.video_id, self.start_sec)

    @property
    def timestamp_label(self) -> str:
        if self.start_sec is None:
            return ""
        m, s = divmod(int(self.start_sec), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["url"] = self.url
        d["timestamp_label"] = self.timestamp_label
        return d


@dataclass
class RelatedVideo:
    """関連動画(なぜ関連するかの一言つき)"""
    video_id: str
    title: str
    channel: str
    thumbnail: str
    reason: str

    @property
    def url(self) -> str:
        return _ts_url(self.video_id, None)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["url"] = self.url
        return d


@dataclass
class AnswerResult:
    """1回の質問に対する構造化結果。回答テキスト本体は別途ストリームで返す。"""
    found: bool
    language: str                                  # "ja" / "en"
    sources: list[SourceVideo] = field(default_factory=list)
    related: list[RelatedVideo] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)  # 例:「字幕なし動画を含む」

    def to_dict(self) -> dict:
        return {
            "found": self.found,
            "language": self.language,
            "sources": [s.to_dict() for s in self.sources],
            "related": [r.to_dict() for r in self.related],
            "notices": self.notices,
        }


NOT_FOUND_MESSAGE = {
    "ja": "アーカイブ内に該当動画が見つかりませんでした。別の言葉で言い換えるか、国・分野フィルタを外して再度お試しください。",
    "en": "No matching videos were found in the archive. Please try rephrasing your question or removing the country/topic filters.",
}

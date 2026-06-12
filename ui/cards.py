"""根拠動画カード / 関連動画カード(HTML描画)。

- カードクリックで該当動画をタイムスタンプ位置から新規タブで開く
- 先頭の根拠動画はアプリ内埋め込み再生(st.video, start_time付き)も提供
"""
from html import escape

from mado_core.schemas import SourceVideo, RelatedVideo


def _card(url: str, thumb: str, title: str, channel: str,
          ts: str = "", reason: str = "", nocap: bool = False) -> str:
    ts_html = f'<span class="mado-ts">▶ {escape(ts)}</span>' if ts else ""
    reason_html = f'<div class="mado-card-reason">{escape(reason)}</div>' if reason else ""
    nocap_html = '<span class="mado-badge-nocap">字幕なし: タイトル・説明文が根拠</span>' if nocap else ""
    return f"""
    <a class="mado-card" href="{escape(url)}" target="_blank" rel="noopener noreferrer"
       aria-label="{escape(title)} をYouTubeで開く">
      <div class="mado-thumbwrap">
        <img src="{escape(thumb)}" alt="" loading="lazy">
        <span class="mado-play">▶</span>
        {ts_html}
      </div>
      <div class="mado-card-body">
        <div class="mado-card-title">{escape(title)}</div>
        <div class="mado-card-ch">{escape(channel)}</div>
        {nocap_html}{reason_html}
      </div>
    </a>"""


def render_sources(st, sources: list[SourceVideo], lang: str):
    if not sources:
        return
    label = "根拠動画" if lang == "ja" else "SOURCE VIDEOS"
    st.markdown(f'<div class="mado-section-label">{label}</div>', unsafe_allow_html=True)
    cards = "".join(
        _card(
            s.url, s.thumbnail, s.title, s.channel,
            ts=s.timestamp_label, nocap=not s.captions_based,
        )
        for s in sources
    )
    st.markdown(f'<div class="mado-cards">{cards}</div>', unsafe_allow_html=True)

    # 先頭の根拠動画はアプリ内で埋め込み再生も可能に(タイムスタンプ位置から)
    top = sources[0]
    exp_label = "このページで再生(根拠動画①)" if lang == "ja" else "Play here (source #1)"
    with st.expander(exp_label):
        try:
            st.video(
                f"https://www.youtube.com/watch?v={top.video_id}",
                start_time=top.start_sec or 0,
            )
        except Exception:
            st.markdown(f"[YouTubeで開く]({top.url})")


def render_related(st, related: list[RelatedVideo], lang: str):
    if not related:
        return
    label = "あわせて見たい関連動画" if lang == "ja" else "RELATED VIDEOS"
    st.markdown(f'<div class="mado-section-label">{label}</div>', unsafe_allow_html=True)
    cards = "".join(
        _card(r.url, r.thumbnail, r.title, r.channel, reason=r.reason)
        for r in related
    )
    # 横スクロール行
    st.markdown(f'<div class="mado-scroll">{cards}</div>', unsafe_allow_html=True)

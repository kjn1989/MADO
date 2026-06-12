"""サイドバー: 国・分野フィルタ + アーカイブ統計 + 言語設定。

語彙は data/catalog.json(索引時に生成)から供給するため、
索引に存在しないタグは選択肢に出ない(=0件フィルタを防ぐ)。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_catalog() -> dict:
    path = os.path.join(ROOT, "data", "catalog.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return {"videos": [], "countries": [], "topics": [], "channels": []}


def render(st) -> tuple[list[str], list[str], str]:
    """return (countries, topics, lang)"""
    cat = load_catalog()
    with st.sidebar:
        st.markdown(
            '<div class="mado-section-label" style="margin-top:2px">アーカイブを絞り込む</div>',
            unsafe_allow_html=True,
        )
        countries = st.multiselect(
            "国・地域", cat["countries"], placeholder="すべての国・地域",
            help="選んだ国・地域に関する動画だけを根拠に回答します",
        )
        topics = st.multiselect(
            "分野", cat["topics"], placeholder="すべての分野",
            help="選んだ分野の動画だけを根拠に回答します",
        )
        lang = st.radio(
            "回答の言語 / Answer language",
            ["auto", "ja", "en"],
            format_func={"auto": "質問の言語に合わせる", "ja": "日本語", "en": "English"}.get,
        )

        n_videos = len(cat["videos"])
        n_cap = sum(1 for v in cat["videos"] if v.get("has_captions"))
        st.markdown(
            f"""
            <div style="margin-top:14px;font-size:12px;line-height:1.8;
                        background:var(--mado-lightblue);border-radius:12px;padding:10px 12px;">
              <b style="color:var(--mado-teal)">アーカイブ統計</b><br>
              チャンネル: {len(cat["channels"])}<br>
              動画: {n_videos:,} 本(うち字幕あり {n_cap:,})<br>
              国・地域タグ: {len(cat["countries"])} / 分野タグ: {len(cat["topics"])}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if n_videos == 0:
            st.warning(
                "索引が空です。先に収集パイプラインを実行してください:\n\n"
                "`python ingestion/run_pipeline.py`"
            )
    return countries, topics, lang

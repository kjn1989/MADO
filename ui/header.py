"""ヘッダー: ロゴ + ワードマーク + タグライン + JICAクレジット(テキスト・常時表示)。"""
import base64
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CREDIT = "Powered by JICA official video archive"


def _logo_b64() -> str:
    path = os.path.join(ROOT, "assets", "logo.svg")
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return ""


def render(st):
    logo = _logo_b64()
    img = (
        f'<img src="data:image/svg+xml;base64,{logo}" width="46" height="46" alt="MADOロゴ: 4分割の窓と朝日">'
        if logo else ""
    )
    st.markdown(
        f"""
        <div class="mado-header">
          {img}
          <div>
            <div class="mado-wordmark">MAD<span class="o">O</span></div>
            <div class="mado-tagline"><b>Meet AI, Discover Opportunities</b> — 世界の“知らなかった”に出会う窓</div>
          </div>
          <div class="mado-credit">{CREDIT}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(st):
    st.markdown(
        f"""
        <div class="mado-footer">
          {CREDIT}<br>
          MADOはJICA(国際協力機構)の公開YouTube動画を情報源とするAIツールです。
          回答はアーカイブ動画の字幕・タイトル・説明文の要約であり、長文の逐語引用は行いません。
          各動画の著作権はJICAに帰属します。回答内容は出典動画でご確認ください。
        </div>
        """,
        unsafe_allow_html=True,
    )

"""MADO デザイントークン + カスタムCSS(Streamlitへ注入)。

ブランド:
  ディープティール #0E5C63 / アンバー #F4A024 / ライトブルー #DCEFFB
シグネチャー要素: 初回画面の「4分割の窓」ヒーロー(窓を開けると世界が見える)。
アクセシビリティ: 本文はティール×白でコントラスト比 7:1 以上、フォーカスリング明示。
"""

TEAL = "#0E5C63"
TEAL_DARK = "#0A444A"
AMBER = "#F4A024"
LIGHTBLUE = "#DCEFFB"
INK = "#12343B"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Montserrat:wght@600;700;800&display=swap');

:root {{
  --mado-teal: {TEAL};
  --mado-teal-dark: {TEAL_DARK};
  --mado-amber: {AMBER};
  --mado-lightblue: {LIGHTBLUE};
  --mado-ink: {INK};
}}

html, body, [class*="css"], .stMarkdown, .stChatMessage {{
  font-family: 'Zen Kaku Gothic New', 'Hiragino Sans', sans-serif;
}}

/* ===== ヘッダー ===== */
.mado-header {{
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  padding: 10px 2px 14px 2px;
  border-bottom: 3px solid var(--mado-lightblue);
  margin-bottom: 4px;
}}
.mado-wordmark {{
  font-family: 'Montserrat', sans-serif;
  font-weight: 800; font-size: 30px; letter-spacing: 0.14em;
  color: var(--mado-teal); line-height: 1;
}}
.mado-wordmark .o {{ color: var(--mado-amber); }}
.mado-tagline {{
  font-size: 13px; color: var(--mado-ink); opacity: .85; line-height: 1.5;
}}
.mado-tagline b {{ color: var(--mado-teal); font-weight: 700; }}
.mado-credit {{
  margin-left: auto; font-size: 11.5px; color: var(--mado-teal);
  background: var(--mado-lightblue); border-radius: 999px; padding: 5px 12px;
  white-space: nowrap; font-weight: 500;
}}
@media (max-width: 640px) {{
  .mado-credit {{ margin-left: 0; }}
}}

/* ===== 初回ヒーロー: 4分割の窓 ===== */
.mado-window {{
  background: var(--mado-teal);
  border-radius: 22px; padding: 14px;
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  box-shadow: 0 10px 30px rgba(14,92,99,.18);
  margin: 10px 0 18px 0;
}}
.mado-pane {{
  background: linear-gradient(180deg, #FFFFFF 0%, var(--mado-lightblue) 100%);
  border-radius: 12px; padding: 18px 16px; min-height: 110px;
  position: relative; overflow: hidden;
}}
.mado-pane.sunrise {{
  background:
    radial-gradient(circle at 50% 115%, var(--mado-amber) 0 26%, #FBD58A 26% 40%, var(--mado-lightblue) 40%),
    var(--mado-lightblue);
  display: flex; flex-direction: column; justify-content: flex-start;
}}
.mado-pane h4 {{ margin: 0 0 6px 0; font-size: 14px; color: var(--mado-teal); font-weight: 700; }}
.mado-pane p  {{ margin: 0; font-size: 12.5px; color: var(--mado-ink); line-height: 1.7; }}
.mado-pane .big {{ font-size: 22px; font-weight: 800; color: var(--mado-teal); font-family: 'Montserrat'; }}

/* ===== 出典・関連動画カード ===== */
.mado-cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 12px; margin: 6px 0 4px 0; }}
.mado-scroll {{ display: flex; gap: 12px; overflow-x: auto; padding: 4px 2px 10px 2px; scrollbar-width: thin; }}
.mado-scroll .mado-card {{ min-width: 230px; max-width: 230px; }}

a.mado-card {{
  display: block; text-decoration: none !important;
  background: #fff; border: 1.5px solid var(--mado-lightblue); border-radius: 14px;
  overflow: hidden; transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}}
a.mado-card:hover, a.mado-card:focus-visible {{
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(14,92,99,.16);
  border-color: var(--mado-amber);
  outline: none;
}}
a.mado-card:focus-visible {{ box-shadow: 0 0 0 3px var(--mado-amber); }}
.mado-thumbwrap {{ position: relative; aspect-ratio: 16/9; background: var(--mado-lightblue); }}
.mado-thumbwrap img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.mado-ts {{
  position: absolute; right: 6px; bottom: 6px;
  background: rgba(10,68,74,.92); color: #fff; font-size: 11px;
  border-radius: 6px; padding: 2px 7px; font-weight: 600;
}}
.mado-play {{
  position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%);
  width: 38px; height: 38px; border-radius: 50%;
  background: rgba(244,160,36,.95); color:#fff;
  display:flex; align-items:center; justify-content:center; font-size:15px;
  box-shadow: 0 2px 8px rgba(0,0,0,.25);
}}
.mado-card-body {{ padding: 10px 12px 12px 12px; }}
.mado-card-title {{
  font-size: 13px; font-weight: 700; color: var(--mado-ink); line-height: 1.45;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 5px; min-height: 2.9em;
}}
.mado-card-ch {{ font-size: 11px; color: var(--mado-teal); font-weight: 600; }}
.mado-card-reason {{
  margin-top: 7px; font-size: 11.5px; color: var(--mado-ink);
  background: var(--mado-lightblue); border-radius: 8px; padding: 5px 8px; line-height: 1.5;
}}
.mado-badge-nocap {{
  display:inline-block; margin-top:6px; font-size:10.5px; color:#7A4E00;
  background:#FDEAC8; border-radius:6px; padding:2px 7px; font-weight:600;
}}
.mado-section-label {{
  font-size: 12.5px; font-weight: 700; color: var(--mado-teal);
  letter-spacing: .06em; margin: 14px 0 4px 0;
  display:flex; align-items:center; gap:7px;
}}
.mado-section-label::before {{
  content:""; width: 14px; height: 14px; border-radius: 4px;
  background:
    linear-gradient(var(--mado-teal), var(--mado-teal)) 50% 0/2px 100% no-repeat,
    linear-gradient(var(--mado-teal), var(--mado-teal)) 0 50%/100% 2px no-repeat,
    var(--mado-lightblue);
  border: 2px solid var(--mado-teal); box-sizing: border-box;
}}

/* ===== チャット ===== */
.stChatMessage {{ border-radius: 16px; }}
[data-testid="stChatMessageAvatarUser"] {{ background-color: var(--mado-amber) !important; }}
[data-testid="stChatMessageAvatarAssistant"] {{ background-color: var(--mado-teal) !important; }}

/* 質問例ボタン */
div[data-testid="stButton"] > button {{
  border: 1.5px solid var(--mado-teal); color: var(--mado-teal);
  border-radius: 999px; font-weight: 600; background: #fff;
}}
div[data-testid="stButton"] > button:hover {{
  border-color: var(--mado-amber); color: var(--mado-teal-dark);
  background: var(--mado-lightblue);
}}

/* フッター */
.mado-footer {{
  margin-top: 28px; padding: 14px 2px; border-top: 1px solid var(--mado-lightblue);
  font-size: 11.5px; color: var(--mado-ink); opacity: .8; line-height: 1.7;
}}

@media (prefers-reduced-motion: reduce) {{
  a.mado-card {{ transition: none; }}
}}
</style>
"""


def inject(st):
    st.markdown(CSS, unsafe_allow_html=True)

"""初回画面: シグネチャー要素「4分割の窓」ヒーロー + 質問例3ボタン。

窓の4枚のガラスにそれぞれ「MADOの説明 / 朝日 / 出典の約束 / アーカイブ規模」を映し、
その下に動作確認用の質問例3つをボタンで提示する。
"""

SUGGESTED = [
    "JICAのインドネシアでの功績が知りたい",
    "アフリカビジネスの好事例を知りたい",
    "水問題って何?",
]


def render(st, n_videos: int) -> str | None:
    """質問例ボタンが押されたらその質問文字列を返す。"""
    st.markdown(
        f"""
        <div class="mado-window" role="img" aria-label="4分割の窓のイラスト。窓を開けると世界が見えるというMADOのコンセプト">
          <div class="mado-pane sunrise">
            <h4>窓を開けよう</h4>
            <p>知らなかった世界・途上国・<br>国際協力の現場が見える。</p>
          </div>
          <div class="mado-pane">
            <h4>JICAの映像が知識のすべて</h4>
            <p>回答はJICA公式YouTube動画の内容だけに基づきます。一般知識での補完はしません。</p>
          </div>
          <div class="mado-pane">
            <h4>出典つきで答えます</h4>
            <p>根拠動画をタイムスタンプ付きで明示。気になったらワンクリックで現場の映像へ。</p>
          </div>
          <div class="mado-pane">
            <h4>アーカイブ</h4>
            <p><span class="big">{n_videos:,}</span> 本の動画<br>8つの公式チャンネルから</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="mado-section-label">こんな質問から開けてみる</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(SUGGESTED))
    clicked = None
    for col, q in zip(cols, SUGGESTED):
        with col:
            if st.button(q, use_container_width=True, key=f"sug_{q}"):
                clicked = q
    return clicked

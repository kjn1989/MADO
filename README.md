# MADO — Meet AI, Discover Opportunities

**世界の“知らなかった”に出会う窓** ｜ Powered by JICA official video archive

MADOは、JICA(国際協力機構)の公式YouTubeチャンネル8つを唯一の知識ソースとするRAG型AIチャットボットです。質問すると、(1) 動画内容からエッセンスを抽出して回答し、(2) 根拠動画をタイムスタンプ付きで明示し、(3) 関連動画を提案します。回答はアーカイブ動画の内容のみに基づき、一般知識での補完は行いません。

本リポジトリは2段構えの第1段階(Streamlit版・無料スタック)です。RAGコアは `mado_core/` にUI非依存パッケージとして分離済みで、第2段階(FastAPI + JICA HP組み込みJSウィジェット)では `api/` がそのまま同じコアを呼びます。

---

## アーキテクチャ概要

```
Streamlit (app.py + ui/)          ← 第1段階のUI層(薄い配線のみ)
        │  mado_core.ask(question, countries, topics, lang)
        ▼
mado_core/                        ← UI非依存のRAGコア
  retriever → 閾値判定 → generator(Gemini) → related
        │                                │
        ▼                                ▼
ChromaDB (data/chroma/)        Google Gemini API (無料枠)
埋め込み: multilingual MiniLM (ローカル・無料)

ingestion/                        ← 収集パイプライン(あなたのPCで実行)
  fetch_videos → fetch_captions → chunk → tag_videos → embed_index
```

第2段階: `api/main.py`(FastAPI)が `mado_core.ask()` をSSEに変換し、`api/widget/mado-widget.js` をJICA HPに1行で埋め込みます。RAGロジックは両段階で完全に共通です。

---

## 1. 必要なAPIキー(どちらも無料)

**YouTube Data API v3**(収集パイプラインで使用)
1. https://console.cloud.google.com でプロジェクト作成
2. 「APIとサービス → ライブラリ」で *YouTube Data API v3* を有効化
3. 「認証情報 → APIキーを作成」でキー取得
4. 無料クォータは1日10,000ユニット。本パイプラインは `playlistItems.list`(1ユニット/50本)中心の設計のため、**8チャンネル全動画の初回収集でも約200ユニット以内**に収まります(`search.list` はハンドル解決の最終フォールバックのみ)

**Google Gemini API**(回答生成・タグ付けで使用)
1. https://aistudio.google.com → 「Get API key」で即時発行
2. 無料枠(gemini-2.0-flash: 目安15リクエスト/分・1,500/日)で動作するようレート制御済み

## 2. セットアップ

```bash
git clone <this-repo> && cd mado
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# torch はCPU版を先に入れると軽量(数百MB節約・Cloudでも有効)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

cp .env.example .env   # YOUTUBE_API_KEY と GEMINI_API_KEY を記入
```

## 3. データ収集・索引(あなたのPCで実行)

**まず小さく動作確認(推奨・約10分):**

```bash
python ingestion/run_pipeline.py --channel-limit 2 --videos-per-channel 20
```

**問題なければ全件(8チャンネル全動画):**

```bash
python ingestion/run_pipeline.py
```

所要時間の目安: 字幕取得が動画数×1〜2秒、タグ付けがGemini無料枠レート制御のため動画数×4.5秒、埋め込みはCPUで数十分。すべて**再実行可能(取得・付与済みはスキップ)**なので、中断しても再開できます。`--skip-tags` でタグ付けを省略し、後から `python ingestion/tag_videos.py` で追加することも可能です。

**全件(約3,306本)での実運用上の注意 — Phase 2:**

- **メタデータ収集**は8チャンネルを1チャンネルごとに途中保存します。中断しても取得済みチャンネルは失われず、再実行で続きから収集します。
- **字幕取得**は、短時間の大量アクセスでYouTube側にかかる一時的なIPレート制限(429 / TooManyRequests 等)を指数バックオフで再試行し、それでも解消しない動画は**結果を保存せずスキップ**します(「字幕なし」として焼き付けない)。実行末尾に「一時失敗 N 本」と表示されたら、数分〜数十分おいて `python ingestion/fetch_captions.py` を再実行すると未取得分だけ自動で取りにいきます。
- **タグ付け**は、Gemini無料枠の**1日あたり上限(目安1,500リクエスト/日)**のため、3,306本を1日で付与しきれません。日次上限に達すると本スクリプトは**空タグを書かずに途中保存して正常終了**します。翌日などに `python ingestion/tag_videos.py` を再実行すれば続きから処理します(付与済みはスキップ)。1回の本数を明示的に絞るには `python ingestion/tag_videos.py --max-per-run 1000` を使います。

> 全件取り込みは「収集 → 字幕(必要なら数回再実行)→ タグ付け(数日に分割)→ 索引」という流れになります。途中の中断・再開は安全で、`run_pipeline.py` を再実行しても済んだ工程はスキップされます。

完了すると `data/chroma/`(ベクトル索引)と `data/catalog.json`(フィルタ用カタログ)が生成されます。

**定期更新(差分クロール):**

```bash
python ingestion/recrawl.py        # 新規公開動画のみ処理
# cron例(毎日4時): 0 4 * * * cd /path/to/mado && .venv/bin/python ingestion/recrawl.py
```

> ⚠️ **GitHub Actions(`.github/workflows/ingest.yml`)についての重要な制限**: YouTubeはクラウド事業者のIP(GitHub Actionsを含む)からの**字幕取得をブロック**します。Actionsで動くのはメタデータ収集・タグ付け・索引化のみで、**字幕は「手元のPCでの実行」または「チャンネル所有者のGoogle Takeoutエクスポート → `data/raw/captions/` へ配置」で供給**してください。字幕なしのまま索引された動画は、字幕が供給された後の索引実行で自動的に置き換わります。所有者権限でのYouTube公式API(`captions.download`)による取得に切り替えれば、Actionsでの完全自動化も可能になります(将来拡張)。

## 4. ローカル起動

```bash
streamlit run app.py
```

http://localhost:8501 が開きます。初回は埋め込みモデルのダウンロード・ロードで1〜2分かかります。

## 5. Streamlit Community Cloud へ無料デプロイ

Community Cloudは再起動でローカルファイルが消えるため、**索引(data/chroma/)をリポジトリに同梱**してデプロイします。

1. `data/chroma/` のサイズを確認: `du -sh data/chroma`
   - **100MB未満**: そのままコミットでOK
   - **100MB超のファイルがある場合**: Git LFSを使用
     ```bash
     git lfs install
     git lfs track "data/chroma/**"
     git add .gitattributes
     ```
2. GitHubへpush(`.env` は `.gitignore` 済み。**キーは絶対にコミットしない**)
3. https://share.streamlit.io → 「New app」→ リポジトリ選択 → Main file: `app.py`
4. アプリの **Settings → Secrets** に以下を設定:
   ```toml
   GEMINI_API_KEY = "あなたのキー"
   ```
   (`YOUTUBE_API_KEY` はCloud側では不要。収集はローカルで行うため)
5. Deploy。初回起動はモデルロードで2〜3分かかります

**メモリが逼迫する場合のフォールバック**(無料インスタンスは約1GB):
- `requirements.txt` のtorchをCPU版に固定(手順2参照)— 既定で対応済み
- それでも落ちる場合は `ingestion/chunk.py` の `TARGET_SEC` を 90→120 に上げてチャンク数を削減し再索引
- 索引が巨大な場合は Hugging Face Datasets に `data/chroma/` をアップロードし、起動時に `huggingface_hub.snapshot_download` でダウンロードする方式に切替可能(app.py冒頭に数行追加)

## 6. 第2段階(JICA HP組み込み)への移行

```bash
pip install fastapi uvicorn
uvicorn api.main:app --port 8000
```

JICA HPのテンプレートに `api/widget/embed-snippet.html` の1行を追加するだけで、右下にMADOチャットウィジェットが表示されます。`api/` はSSE変換のみの薄い層で、RAGの振る舞いはStreamlit版と完全に同一です。本番では `MADO_ALLOWED_ORIGINS` を `https://www.jica.go.jp` に設定し、ChromaDBが規模的に不足する場合は `mado_core/vectorstore.py` の3関数をpgvector実装に差し替えます(他のコードは無変更)。

---

## チャットボットの振る舞い(実装上の保証)

**ハルシネーション防止は二重構造**です。第一関門: 類似度閾値(`MADO_SIM_THRESHOLD`、既定0.35)を超える根拠チャンクが1つも無ければLLMを呼ばずに「アーカイブ内に該当動画が見つかりませんでした」を返します。第二関門: プロンプトで根拠外知識の使用を禁止し、**出典カードはLLM出力ではなくretrieverの結果から機械的に組み立てる**ため、出典の捏造が構造的に起こりません。

字幕の無い動画はタイトル・説明文のみを索引(`source_type: metadata_only`)し、回答・カードの両方で「字幕なし」を明示します。自動字幕の誤認識リスクには、公式字幕を再ランキングでわずかに優遇することで対処しています。多言語マッチングはmultilingual MiniLM埋め込みにより、日本語の質問で英語チャンネル(JICA Global / Ethiopia / Palestine等)の動画もヒットします。回答言語は質問の言語に自動追従します(サイドバーで固定も可)。

長文の逐語引用は行わず要約+出典リンクで応答し、「Powered by JICA official video archive」を常時表示します(JICA公式ロゴ画像は不使用)。

## 設定リファレンス(環境変数)

| 変数 | 既定値 | 説明 |
|---|---|---|
| `GEMINI_API_KEY` | — | 必須(生成・タグ付け) |
| `YOUTUBE_API_KEY` | — | 収集時のみ必須 |
| `MADO_GEMINI_MODEL` | `gemini-2.0-flash` | 生成モデル差し替え |
| `MADO_EMBED_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | 埋め込み差し替え(変更時は再索引) |
| `MADO_SIM_THRESHOLD` | `0.35` | 「該当なし」判定の類似度閾値 |
| `MADO_MAX_SOURCES` | `3` | 根拠動画数の上限 |
| `MADO_RELATED` | `4` | 関連動画の提示数(2〜4) |

## ディレクトリ構成

```
app.py            Streamlitエントリポイント(UI配線のみ)
ui/               Streamlit専用UI部品(第2段階では未使用)
mado_core/        UI非依存RAGコア(第2段階で完全流用)
ingestion/        収集パイプライン(ローカル実行)
data/chroma/      ベクトル索引(デプロイのためコミット対象)
data/catalog.json フィルタUI用カタログ
assets/           ロゴ・ファビコン(オリジナルSVG)
api/              第2段階用FastAPI + JSウィジェット雛形
```

## 既知の制限

自動字幕には誤認識が含まれるため、回答は出典動画での確認を前提としたツールです。Gemini無料枠のレート制限(15RPM)時は自動リトライしますが、デモで連続質問する場合は数秒間隔を空けてください。Streamlit Community Cloudは一定期間アクセスが無いとスリープし、再アクセス時の起動に1〜2分かかります(広報部デモの直前に一度アクセスしておくことを推奨します)。

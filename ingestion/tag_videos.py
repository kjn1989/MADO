"""Step 4: Gemini で国・分野タグを付与 → data/raw/tags.json

- 1動画1回のみ(再実行時は付与済みをスキップ)
- 分野は統制語彙(下記TOPICS)から選択させ、フィルタUIの語彙ブレを防ぐ
- レート制限(無料枠 15RPM 目安)に合わせて 4.5 秒間隔

全件(3,306本)取得時の注意:
  Gemini 無料枠は分速(RPM)に加えて 1日あたりのリクエスト上限(目安 1,500/日)が
  あるため、3,306本を1日では付与しきれない。日次上限に達すると 429
  (ResourceExhausted)が返り続ける。これを「内容エラー」と混同して空タグ
  ({"countries":[],"topics":[]})を書いてしまうと、その動画は付与済み扱いとなり
  二度とタグ付けされず、国・分野フィルタが半分以上欠落する。
  そこで本スクリプトは:
    - 一時的なRPM超過は指数バックオフで再試行する
    - 再試行でも解消しないレート/クォータ系エラーは「日次上限の枯渇」とみなし、
      空タグを書かずに途中保存して正常終了する(翌日などに再実行すれば続きから処理)
    - 解析エラー等の真の失敗のみ空タグで継続する
  1回の実行で付与本数を制限したい場合は --max-per-run を使う。
"""
from __future__ import annotations

import json
import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

TOPICS = [
    "水・衛生", "保健医療", "教育", "農業・食料", "防災", "気候変動・環境",
    "インフラ", "ICT・デジタル", "民間連携・ビジネス", "平和構築", "ジェンダー",
    "海外協力隊", "研究・政策", "文化・スポーツ", "エネルギー", "ガバナンス",
]

PROMPT = """次のYouTube動画のタイトルと説明文から、関係する「国名」と「分野」を抽出してください。
分野は必ず次のリストから選ぶこと: {topics}
国名は日本語の正式な通称(例: インドネシア, エチオピア, パレスチナ)。特定の国がなければ空配列。
JSONのみを出力(マークダウン記法・前置き禁止):
{{"countries": ["..."], "topics": ["..."]}}

タイトル: {title}
説明文: {desc}"""

# レート/クォータ系エラー(時間や日をおけば回復しうる)を判定するキーワード
RATE_KEYS = (
    "429", "resourceexhausted", "resource exhausted", "exhaust", "quota",
    "rate limit", "ratelimit", "too many requests", "503", "service unavailable",
    "unavailable", "deadline",
)
TAG_RETRIES = 4      # RPM超過などの一時的レート制限の再試行回数
BACKOFF_BASE = 5     # 指数バックオフ基準秒(5,10,20,40)


def _is_rate_error(exc: Exception) -> bool:
    blob = f"{type(exc).__name__} {exc}".lower()
    return any(k in blob for k in RATE_KEYS)


def _save(tags: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False)


def _tag_one(model, v: dict) -> dict | None:
    """1動画にタグ付けし dict を返す。

    返り値:
      dict  … 付与成功、または解析エラー時の空タグ(いずれも保存してよい)
      None  … レート/クォータ制限が再試行でも解消せず(日次上限の枯渇とみなす)。
              呼び出し側は空タグを書かずに中断する。
    """
    for attempt in range(TAG_RETRIES + 1):
        try:
            resp = model.generate_content(
                PROMPT.format(topics=", ".join(TOPICS),
                              title=v["title"], desc=(v.get("description") or "")[:800]),
                generation_config={"temperature": 0.0, "max_output_tokens": 200},
            )
            raw = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            d = json.loads(raw)
            return {
                "countries": [c for c in d.get("countries", []) if isinstance(c, str)][:5],
                "topics": [t for t in d.get("topics", []) if t in TOPICS][:4],
            }
        except Exception as e:
            if _is_rate_error(e):
                if attempt < TAG_RETRIES:
                    wait = BACKOFF_BASE * (2 ** attempt)
                    print(f"  [{v['video_id']}] レート/クォータ制限: {wait}秒待機して再試行 "
                          f"({attempt + 1}/{TAG_RETRIES})")
                    time.sleep(wait)
                    continue
                # 再試行しても解消しない = その日の無料枠を使い切った可能性が高い
                print(f"  [{v['video_id']}] レート/クォータ制限が解消しません: {e}")
                return None
            # 解析エラー等の真の失敗のみ空タグで継続(再取得を省く)
            print(f"  [{v['video_id']}] tag失敗(内容エラー): {e} → 空タグで継続")
            return {"countries": [], "topics": []}


def main(max_per_run: int | None = None):
    load_dotenv(os.path.join(ROOT, ".env"))
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(os.getenv("MADO_GEMINI_MODEL", "gemini-2.0-flash"))

    with open(os.path.join(RAW, "videos.json"), encoding="utf-8") as f:
        videos = json.load(f)

    tags_path = os.path.join(RAW, "tags.json")
    tags = {}
    if os.path.exists(tags_path):
        with open(tags_path, encoding="utf-8") as f:
            tags = json.load(f)

    todo = [v for v in videos if v["video_id"] not in tags]
    print(f"タグ付け対象: {len(todo)} 本(付与済み {len(tags)} 本はスキップ)")

    done = 0
    for i, v in enumerate(todo, 1):
        tag = _tag_one(model, v)
        if tag is None:
            # 日次クォータ枯渇とみなし、空タグを書かずに途中保存して正常終了
            _save(tags, tags_path)
            print(f"日次クォータに達した可能性があります。"
                  f"途中保存しました(付与済み {len(tags)} 本)。"
                  f"時間/日をおいて再実行すると続きから処理します。")
            return
        tags[v["video_id"]] = tag
        done += 1

        if done % 10 == 0:
            _save(tags, tags_path)
            print(f"  {done}/{len(todo)} 完了(途中保存)")
        if max_per_run and done >= max_per_run:
            _save(tags, tags_path)
            print(f"--max-per-run={max_per_run} に到達。途中保存して終了"
                  f"(残り {len(todo) - done} 本は再実行で続行)。")
            return
        time.sleep(4.5)  # 無料枠 15RPM 対策

    _save(tags, tags_path)
    print(f"完了 → {tags_path}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--max-per-run", type=int, default=None,
                   help="1回の実行で付与する最大本数(日次無料枠内に収めたい場合に指定)")
    a = p.parse_args()
    main(a.max_per_run)

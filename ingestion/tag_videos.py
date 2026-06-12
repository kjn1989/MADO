"""Step 4: Gemini で国・分野タグを付与 → data/raw/tags.json

- 1動画1回のみ(再実行時は付与済みをスキップ)→ 無料枠で十分賄える
- 分野は統制語彙(下記TOPICS)から選択させ、フィルタUIの語彙ブレを防ぐ
- レート制限(無料枠 15RPM 目安)に合わせて 4.5 秒間隔
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


def main():
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

    for i, v in enumerate(todo, 1):
        try:
            resp = model.generate_content(
                PROMPT.format(topics=", ".join(TOPICS),
                              title=v["title"], desc=(v.get("description") or "")[:800]),
                generation_config={"temperature": 0.0, "max_output_tokens": 200},
            )
            raw = resp.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            d = json.loads(raw)
            tags[v["video_id"]] = {
                "countries": [c for c in d.get("countries", []) if isinstance(c, str)][:5],
                "topics": [t for t in d.get("topics", []) if t in TOPICS][:4],
            }
        except Exception as e:
            print(f"  [{v['video_id']}] tag失敗: {e} → 空タグで継続")
            tags[v["video_id"]] = {"countries": [], "topics": []}

        if i % 10 == 0:
            with open(tags_path, "w", encoding="utf-8") as f:
                json.dump(tags, f, ensure_ascii=False)
            print(f"  {i}/{len(todo)} 完了(途中保存)")
        time.sleep(4.5)  # 無料枠 15RPM 対策

    with open(tags_path, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False)
    print(f"完了 → {tags_path}")


if __name__ == "__main__":
    main()

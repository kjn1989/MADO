"""Generator: Gemini を呼び、根拠チャンク限定で回答をストリーム生成する。

ハルシネーション防止の第二関門: プロンプトで根拠外の知識使用を禁止し、
出典カードは LLM 出力ではなく retriever の結果から機械的に組み立てる
(= 出典の捏造が構造的に起こらない)。
"""
from __future__ import annotations

import re
import time
from typing import Iterator

from .config import get_settings
from .prompts import SYSTEM, USER_TEMPLATE, format_context

_JA_RE = re.compile(r"[ぁ-んァ-ヶ一-龯]")


def detect_language(text: str) -> str:
    """質問の言語を判定(日本語文字を含めば ja)。"""
    return "ja" if _JA_RE.search(text) else "en"


def stream_answer(question: str, chunks: list[dict], lang: str) -> Iterator[str]:
    """回答テキストをトークン単位で yield。Gemini無料枠のレート制限(429)は
    指数バックオフで最大2回リトライする。"""
    import google.generativeai as genai

    s = get_settings()
    genai.configure(api_key=s.gemini_api_key)
    model = genai.GenerativeModel(s.gemini_model, system_instruction=SYSTEM[lang])
    prompt = USER_TEMPLATE[lang].format(
        question=question, context=format_context(chunks)
    )

    delay = 4
    for attempt in range(3):
        try:
            resp = model.generate_content(
                prompt,
                stream=True,
                generation_config={"temperature": 0.3, "max_output_tokens": 1024},
            )
            for part in resp:
                if part.text:
                    yield part.text
            return
        except Exception as e:
            msg = str(e)
            if attempt < 2 and ("429" in msg or "quota" in msg.lower() or "rate" in msg.lower()):
                wait_note = (
                    f"\n\n_(無料枠のアクセス集中のため {delay} 秒待機しています…)_\n\n"
                    if lang == "ja"
                    else f"\n\n_(Free-tier rate limit hit — retrying in {delay}s…)_\n\n"
                )
                yield wait_note
                time.sleep(delay)
                delay *= 2
                continue
            raise

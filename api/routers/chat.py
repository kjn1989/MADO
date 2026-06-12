"""POST /api/chat — mado_core.ask() の結果をSSEで配信する。

イベント仕様(JSウィジェット mado-widget.js と対):
  event: meta    data: AnswerResult の JSON(sources / related / notices / found)
  event: token   data: 回答テキストの断片(複数回)
  event: done    data: {}
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import mado_core
from mado_core.schemas import NOT_FOUND_MESSAGE

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    countries: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    lang: str = "auto"


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
def chat(req: ChatRequest):
    result, stream = mado_core.ask(
        req.question, countries=req.countries, topics=req.topics, lang=req.lang
    )

    def gen():
        yield _sse("meta", result.to_dict())
        if not result.found:
            yield _sse("token", NOT_FOUND_MESSAGE[result.language])
        else:
            for token in stream:
                yield _sse("token", token)
        yield _sse("done", {})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

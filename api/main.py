"""MADO API — 第2段階(JICA HP組み込み)用 FastAPI。

★第1段階では使用しません(Streamlit版はこのファイルを一切importしない)。
mado_core.ask() をSSEに変換するだけの薄い層であることに注意。
RAGロジックは1行も持たない = Streamlit版と完全に同一の振る舞いを保証。

起動(第2段階):
  pip install fastapi uvicorn sse-starlette
  uvicorn api.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import chat

app = FastAPI(title="MADO API", version="0.1.0")

# JICA HP からのウィジェット呼び出しを許可(本番では正確なオリジンに限定)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("MADO_ALLOWED_ORIGINS", "https://www.jica.go.jp").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "mado-api"}

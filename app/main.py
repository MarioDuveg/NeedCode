from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .judge import SubmissionRejected, judge
from .problems import PROBLEMS, public_problem

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AlgoGrader", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class SubmitRequest(BaseModel):
    problem: str
    code: str = Field(min_length=1, max_length=20_000)


# Lightweight in-memory abuse protection. It resets when the Render instance restarts.
_RATE_WINDOW_SECONDS = 60
_RATE_MAX = 12
_rate: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = Lock()


def _check_rate_limit(request: Request) -> None:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip:
        ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _rate_lock:
        q = _rate[ip]
        while q and now - q[0] > _RATE_WINDOW_SECONDS:
            q.popleft()
        if len(q) >= _RATE_MAX:
            raise HTTPException(status_code=429, detail="Demasiados envíos. Intenta de nuevo en un minuto.")
        q.append(now)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/problems")
def list_problems() -> list[dict]:
    return [public_problem(problem) for problem in PROBLEMS.values()]


@app.get("/api/problems/{slug}")
def get_problem(slug: str) -> dict:
    problem = PROBLEMS.get(slug)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problema no encontrado.")
    return public_problem(problem)


@app.post("/api/submit")
def submit(body: SubmitRequest, request: Request) -> dict:
    _check_rate_limit(request)
    problem = PROBLEMS.get(body.problem)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problema no encontrado.")
    try:
        return judge(problem, body.code)
    except SubmissionRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

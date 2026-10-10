import sqlite3
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="文字实验室 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://profile.m3u8player.com.cn", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(__file__).parent / "data" / "app.db"
COOKIE_NAME = "lab_session"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                text TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                word_count INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


init_db()


def save_analysis(session_id: str, text: str, char_count: int, word_count: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO analyses (session_id, text, char_count, word_count) VALUES (?, ?, ?, ?)",
            (session_id, text, char_count, word_count),
        )


def get_recent(session_id: str, limit: int = 5) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, text, char_count, word_count, created_at
            FROM analyses
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_or_create_session(request: Request, response: Response) -> str:
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        session_id = uuid.uuid4().hex
        response.set_cookie(
            key=COOKIE_NAME,
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,  # 30 天
        )
    return session_id


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    char_count: int
    char_no_space: int
    word_count: int
    chinese_count: int
    reversed_text: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest, request: Request, response: Response):
    session_id = get_or_create_session(request, response)

    text = req.text
    trimmed = text.strip()

    char_count = len(text)
    char_no_space = len("".join(text.split()))
    word_count = len(trimmed.split()) if trimmed else 0
    chinese_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fa5")
    reversed_text = text[::-1]

    save_analysis(session_id, text, char_count, word_count)

    return AnalyzeResponse(
        char_count=char_count,
        char_no_space=char_no_space,
        word_count=word_count,
        chinese_count=chinese_count,
        reversed_text=reversed_text,
    )


@app.get("/api/history")
def history(request: Request, response: Response):
    session_id = get_or_create_session(request, response)
    return {"items": get_recent(session_id, 5)}
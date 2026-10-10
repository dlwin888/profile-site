import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="文字实验室 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://profile.m3u8player.com.cn"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(__file__).parent / "data" / "app.db"


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
                text TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                word_count INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


init_db()


def save_analysis(text: str, char_count: int, word_count: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO analyses (text, char_count, word_count) VALUES (?, ?, ?)",
            (text, char_count, word_count),
        )


def get_recent(limit: int = 5) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, text, char_count, word_count, created_at
            FROM analyses
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


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
def analyze(req: AnalyzeRequest):
    text = req.text
    trimmed = text.strip()

    char_count = len(text)
    char_no_space = len("".join(text.split()))
    word_count = len(trimmed.split()) if trimmed else 0
    chinese_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fa5")
    reversed_text = text[::-1]

    save_analysis(text, char_count, word_count)

    return AnalyzeResponse(
        char_count=char_count,
        char_no_space=char_no_space,
        word_count=word_count,
        chinese_count=chinese_count,
        reversed_text=reversed_text,
    )


@app.get("/api/history")
def history():
    return {"items": get_recent(5)}
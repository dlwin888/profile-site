import sqlite3
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="零到全栈 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://profile.m3u8player.com.cn", "http://localhost:3000"],
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

def get_or_create_session(request: Request, response: Response) -> str:
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        session_id = uuid.uuid4().hex
        response.set_cookie(
            key=COOKIE_NAME, value=session_id,
            httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30,
        )
    return session_id

# ================= 接口定义 =================

@app.get("/api/profile")
def get_profile():
    # 教程要求：主页的标题、副标题、作品和座右铭来自 API
    return {
        "heroTitle": "你好，我是段乐",
        "heroSubtitle": "项目，创意，灵感，心得，我的作品",
        "featuredWork": {
            "kicker": "作品",
            "title": "文字实验室",
            "copy": "拼音和情绪，挖掘中文里的细节",
            "linkLabel": "打开作品"
        },
        "identity": {
            "motto": "已识乾坤大，尤怜草木青",
            "learning": "零到全栈"
        }
    }

class AnalyzeRequest(BaseModel):
    text: str

@app.post("/api/analyze")
def analyze(req: AnalyzeRequest, request: Request, response: Response):
    session_id = get_or_create_session(request, response)
    text = req.text
    
    char_count = len(text)
    word_count = len(text.strip().split()) if text.strip() else 0
    
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO analyses (session_id, text, char_count, word_count) VALUES (?, ?, ?, ?)",
            (session_id, text, char_count, word_count),
        )
        
    return {
        "char_count": char_count,
        "word_count": word_count,
        "reversed_text": text[::-1]
    }

@app.get("/api/history")
def get_history(request: Request, response: Response):
    session_id = get_or_create_session(request, response)
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, text, char_count, created_at FROM analyses WHERE session_id = ? ORDER BY id DESC LIMIT 20",
            (session_id,),
        ).fetchall()
    return {"items": [dict(r) for r in rows]}
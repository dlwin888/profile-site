import sqlite3
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from zhipuai import ZhipuAI

app = FastAPI(title="零到全栈 API")
# 初始化限流器，按客户端 IP 地址进行限制
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
@limiter.limit("5/minute")  # 👈 新增：每分钟最多 5 次
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

@app.delete("/api/history/{item_id}")
def delete_history(item_id: int, request: Request):
    # 获取当前用户的 session_id
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")

    with get_conn() as conn:
        # 核心安全逻辑：必须同时匹配 id 和 session_id 才能删除
        cursor = conn.execute(
            "DELETE FROM analyses WHERE id = ? AND session_id = ?",
            (item_id, session_id)
        )
        
        # 如果影响行数为 0，说明这条记录不存在，或者不属于当前用户
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="记录不存在或无权限删除")

    return {"status": "ok", "message": "删除成功"}

# 初始化客户端 (会自动读取 ZHIPUAI_API_KEY 环境变量)
# 如果没有环境变量，也可以在 ZhipuAI(api_key="your-key") 中指定
zhipu_client = ZhipuAI()

class AIRequest(BaseModel):
    text: str

@app.post("/api/ai-analyze")
@limiter.limit("5/minute") # 同样加上限流保护
def ai_analyze(req: AIRequest, request: Request):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    try:
        response = zhipu_client.chat.completions.create(
            model="glm-4-flash", # 使用免费模型
            messages=[
                {"role": "system", "content": "你是一个文本分析专家。请对用户提供的文本进行情感分析、关键词提取和一句话总结。请用简洁的格式返回。"},
                {"role": "user", "content": req.text}
            ],
            stream=False, # 暂时使用非流式，响应快
        )
        ai_result = response.choices[0].message.content
        return {"result": ai_result}
    
    except Exception as e:
        print(f"AI调用失败: {e}")
        raise HTTPException(status_code=500, detail="AI 服务暂时不可用")
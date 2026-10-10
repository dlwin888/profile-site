from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="文字实验室 API")

# 允许本地前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://profile.m3u8player.com.cn"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    return AnalyzeResponse(
        char_count=char_count,
        char_no_space=char_no_space,
        word_count=word_count,
        chinese_count=chinese_count,
        reversed_text=reversed_text,
    )
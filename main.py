from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List

# 뉴스 API 클라이언트, GPT 요약기 임포트
from utils import news_api
from utils import summarize

app = FastAPI()

# 정적 파일 연결
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ──────────────────────────────────────────────
# 뉴스 API & GPT 요약 클라이언트 초기화
# ──────────────────────────────────────────────
news_client = news_api.NewsAPIClient()
summarizer = summarize.Summarizer()

# ──────────────────────────────────────────────
# 메인 화면 (최신 뉴스 5개)
# ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, country: str = "kr", category: Optional[str] = None):
    """
    최신 헤드라인 5개 가져오기
    """
    try:
        articles: List[news_api.Article] = news_client.top_headlines(country=country, category=category, page_size=5)
    except Exception as e:
        articles = []
        print(f"뉴스 API 호출 실패: {e}")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "articles": articles
        }
    )

# ──────────────────────────────────────────────
# 뉴스 요약 화면
# ──────────────────────────────────────────────
@app.get("/summary", response_class=HTMLResponse)
async def read_summary(
    request: Request,
    title: str = Query(...),
    description: Optional[str] = Query(None),
    url: Optional[str] = Query(None)
):
    """
    기사 제목/설명/URL 기반 GPT 3줄 요약 생성
    """
    try:
        summary_text = summarizer.summarize_3lines(title=title, description=description or "", url=url)
    except Exception as e:
        summary_text = f"요약 생성 실패: {e}"

    return templates.TemplateResponse(
        "summary.html",
        {
            "request": request,
            "title": title,
            "summary": summary_text,
            "url": url
        }
    )

# ──────────────────────────────────────────────
# 뉴스 검색 기능
# ──────────────────────────────────────────────
@app.get("/search", response_class=HTMLResponse)
async def search_news(request: Request, keyword: str = Query(..., min_length=1)):
    """
    검색어 기반 뉴스 검색 (최대 5개)
    """
    try:
        articles: List[news_api.Article] = news_client.search(query=keyword, page_size=5)
    except Exception as e:
        articles = []
        print(f"뉴스 검색 실패: {e}")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "articles": articles
        }
    )

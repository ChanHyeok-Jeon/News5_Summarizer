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
async def read_root(
    request: Request,
    page: int = Query(1, ge=1, le=3),   # 페이지 번호 (1~3 사이)
    country: str = "kr",
    category: Optional[str] = None
):
    """
    최신 헤드라인 30개 가져오기 → 10개씩 페이지로 분할
    """
    try:
        articles: List[news_api.Article] = news_client.top_headlines(
            country=country, category=category, page_size=30
        )
    except Exception as e:
        articles = []
        print(f"뉴스 API 호출 실패: {e}")

    # 페이지네이션 처리 (10개씩 분할)
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    page_articles = articles[start:end]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "articles": page_articles,
            "page": page,
            "total_pages": 3
        }
    )

# ──────────────────────────────────────────────
# 뉴스 요약 화면
# ──────────────────────────────────────────────
@app.get("/summary", response_class=HTMLResponse)
async def read_summary(
    request: Request,
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    url: Optional[str] = Query(None)
):
    """
    기사 제목/설명/URL 기반 GPT 3줄 요약 생성
    """
    try:
        summary_text = summarizer.summarize_3lines(
            title=title or "제목 없음",
            description=description or "",
            url=url
        )
    except Exception as e:
        summary_text = f"요약 생성 실패: {e}"

    return templates.TemplateResponse(
        "summary.html",
        {
            "request": request,
            "title": title or "제목 없음",
            "summary": summary_text,
            "url": url
        }
    )

# ──────────────────────────────────────────────
# 뉴스 검색 기능
# ──────────────────────────────────────────────
@app.get("/search", response_class=HTMLResponse)
async def search_news(request: Request, keyword: str, page: int = 1):
    try:
        articles: List[news_api.Article] = news_client.search(
            query=keyword, page_size=30
        )
    except Exception as e:
        print(f"뉴스 검색 실패: {e}")
        articles = []

    # 페이지네이션 (10개씩)
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    page_articles = articles[start:end]

    total_pages = (len(articles) + per_page - 1) // per_page or 1

    return templates.TemplateResponse(
    "index.html",
    {
        "request": request,
        "articles": page_articles,
        "keyword": keyword,  # ✅ 템플릿에서 사용
        "page": page,
        "total_pages": total_pages,
    }
)



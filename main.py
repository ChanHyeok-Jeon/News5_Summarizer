from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import logging
import asyncio
from contextlib import asynccontextmanager

# 뉴스 API 클라이언트, GPT 요약기 임포트
from utils import news_api
from utils import summarize

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 전역 변수
# ──────────────────────────────────────────────
news_client = None
summarizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 리소스 초기화/정리"""
    global news_client, summarizer
    
    # 시작 시 초기화
    try:
        logger.info("🚀 뉴스 API 및 요약기 초기화 중...")
        news_client = news_api.NewsAPIClient()
        summarizer = summarize.Summarizer()
        logger.info("✅ 초기화 완료")
    except Exception as e:
        logger.error(f"❌ 초기화 실패: {e}")
        # 서비스는 계속 실행하되, 기능이 제한됨을 표시
        news_client = None
        summarizer = None
    
    yield
    
    # 종료 시 정리 (필요한 경우)
    logger.info("🔄 서비스 종료 중...")

# ──────────────────────────────────────────────
# FastAPI 앱 생성
# ──────────────────────────────────────────────
app = FastAPI(
    title="📰 News Summarizer",
    description="AI 기반 뉴스 요약 서비스",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 (필요시)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ──────────────────────────────────────────────
# 유틸리티 함수들
# ──────────────────────────────────────────────
async def get_news_articles(
    country: str = "kr",
    category: Optional[str] = None,
    query: Optional[str] = None,
    page_size: int = 30
) -> List[news_api.Article]:
    """뉴스 기사 가져오기 (비동기)"""
    if not news_client:
        return []
    
    try:
        # asyncio를 사용해 블로킹 호출을 비동기로 처리
        if query:
            articles = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: news_client.search(query=query, page_size=page_size)
            )
        else:
            articles = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: news_client.top_headlines(
                    country=country, 
                    category=category, 
                    page_size=page_size
                )
            )
        return articles
    except Exception as e:
        logger.error(f"뉴스 API 호출 실패: {e}")
        return []

def paginate_articles(
    articles: List[news_api.Article], 
    page: int, 
    per_page: int = 10
) -> tuple[List[news_api.Article], int]:
    """기사 목록 페이지네이션"""
    total_pages = max(1, (len(articles) + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    page_articles = articles[start:end]
    return page_articles, total_pages

# ──────────────────────────────────────────────
# 라우트 핸들러들
# ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request,
    page: int = Query(1, ge=1, le=10, description="페이지 번호"),
    country: str = Query("kr", description="국가 코드"),
    category: Optional[str] = Query(None, description="뉴스 카테고리")
):
    """메인 화면 - 최신 헤드라인"""
    logger.info(f"📱 메인 페이지 요청: page={page}, country={country}, category={category}")
    
    # 뉴스 기사 가져오기
    articles = await get_news_articles(
        country=country, 
        category=category, 
        page_size=30
    )
    
    # 페이지네이션 적용
    page_articles, total_pages = paginate_articles(articles, page)
    
    logger.info(f"✅ {len(page_articles)}개 기사 반환 (총 {len(articles)}개)")
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "articles": page_articles,
            "page": page,
            "total_pages": total_pages,
            "keyword": None  # 검색이 아니므로 None
        }
    )

@app.get("/search", response_class=HTMLResponse)
async def search_news(
    request: Request, 
    keyword: str = Query(..., min_length=1, max_length=100, description="검색 키워드"),
    page: int = Query(1, ge=1, le=10, description="페이지 번호")
):
    """뉴스 검색"""
    logger.info(f"🔍 검색 요청: keyword='{keyword}', page={page}")
    
    # 뉴스 검색 실행
    articles = await get_news_articles(query=keyword, page_size=30)
    
    # 페이지네이션 적용
    page_articles, total_pages = paginate_articles(articles, page)
    
    logger.info(f"✅ '{keyword}' 검색결과: {len(page_articles)}개 (총 {len(articles)}개)")
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "articles": page_articles,
            "keyword": keyword,
            "page": page,
            "total_pages": total_pages
        }
    )

@app.get("/summary", response_class=HTMLResponse)
async def read_summary(
    request: Request,
    title: Optional[str] = Query(None, description="뉴스 제목"),
    description: Optional[str] = Query(None, description="뉴스 설명"),
    url: Optional[str] = Query(None, description="뉴스 URL")
):
    """뉴스 요약 화면"""
    logger.info(f"📄 요약 페이지 요청: title='{title[:50] if title else None}...'")
    
    # 필수 정보 검증
    if not title:
        raise HTTPException(status_code=400, detail="뉴스 제목이 필요합니다")
    
    # 요약 생성
    summary_text = "요약을 생성하는 중입니다..."
    
    if summarizer:
        try:
            # 비동기로 요약 생성
            summary_text = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: summarizer.summarize_3lines(
                    title=title,
                    description=description or "",
                    url=url
                )
            )
            logger.info("✅ 요약 생성 완료")
        except Exception as e:
            logger.error(f"❌ 요약 생성 실패: {e}")
            summary_text = f"요약 생성 중 오류가 발생했습니다: {str(e)}"
    else:
        summary_text = "요약 서비스가 일시적으로 사용할 수 없습니다"
    
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
# API 엔드포인트들 (AJAX 호출용)
# ──────────────────────────────────────────────
@app.get("/api/news", response_class=JSONResponse)
async def api_get_news(
    country: str = Query("kr", description="국가 코드"),
    category: Optional[str] = Query(None, description="카테고리"),
    query: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, le=10),
    per_page: int = Query(10, ge=1, le=20)
):
    """뉴스 API (JSON 응답)"""
    try:
        articles = await get_news_articles(
            country=country,
            category=category,
            query=query,
            page_size=per_page * 5  # 더 많이 가져와서 페이지네이션
        )
        
        page_articles, total_pages = paginate_articles(articles, page, per_page)
        
        # Article 객체를 dict로 변환
        articles_data = [
            {
                "title": article.title,
                "description": article.description,
                "url": article.url,
                "urlToImage": article.urlToImage,
                "source_name": article.source_name,
                "published_at": article.published_at
            }
            for article in page_articles
        ]
        
        return {
            "success": True,
            "data": {
                "articles": articles_data,
                "page": page,
                "total_pages": total_pages,
                "total_count": len(articles)
            }
        }
    except Exception as e:
        logger.error(f"API 뉴스 조회 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/summarize", response_class=JSONResponse)
async def api_summarize(
    request_data: Dict[str, Any]
):
    """뉴스 요약 API (JSON 응답)"""
    try:
        title = request_data.get("title")
        description = request_data.get("description")
        url = request_data.get("url")
        
        if not title:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "제목이 필요합니다"}
            )
        
        if not summarizer:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "요약 서비스가 사용할 수 없습니다"}
            )
        
        # 비동기 요약 생성
        summary = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: summarizer.summarize_3lines(
                title=title,
                description=description,
                url=url
            )
        )
        
        return {
            "success": True,
            "data": {
                "summary": summary,
                "title": title
            }
        }
        
    except Exception as e:
        logger.error(f"API 요약 생성 실패: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# ──────────────────────────────────────────────
# 헬스 체크 및 상태 확인
# ──────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    status = {
        "status": "healthy",
        "services": {
            "news_api": news_client is not None,
            "summarizer": summarizer is not None
        }
    }
    
    # 하나라도 실패하면 degraded 상태
    if not all(status["services"].values()):
        status["status"] = "degraded"
    
    return status

@app.get("/api/categories")
async def get_categories():
    """사용 가능한 뉴스 카테고리 목록"""
    categories = [
        {"id": "business", "name": "비즈니스"},
        {"id": "entertainment", "name": "엔터테인먼트"},
        {"id": "general", "name": "일반"},
        {"id": "health", "name": "건강"},
        {"id": "science", "name": "과학"},
        {"id": "sports", "name": "스포츠"},
        {"id": "technology", "name": "기술"}
    ]
    
    return {"success": True, "data": categories}

# ──────────────────────────────────────────────
# 에러 핸들링
# ──────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404 에러 처리"""
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 404,
            "error_message": "페이지를 찾을 수 없습니다",
            "home_url": "/"
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """500 에러 처리"""
    logger.exception("서버 내부 오류 발생")
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "error_code": 500,
            "error_message": "서버 내부 오류가 발생했습니다",
            "home_url": "/"
        },
        status_code=500
    )

# ──────────────────────────────────────────────
# 개발용 실행
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
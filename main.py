from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# 정적 파일 연결
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 가짜 뉴스 데이터
dummy_articles = [
    {"title": "AI가 세상을 바꾸다", "url": "/summary?title=AI가 세상을 바꾸다"},
    {"title": "클라우드 시대의 보안", "url": "/summary?title=클라우드 시대의 보안"},
    {"title": "Python, 개발자들이 사랑하는 언어", "url": "/summary?title=Python"},
    {"title": "Kubernetes로 배우는 운영 자동화", "url": "/summary?title=Kubernetes"},
    {"title": "데이터 사이언스 최신 동향", "url": "/summary?title=데이터 사이언스"},
]

# 메인 화면 (검색 결과 + 뉴스 5개)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "articles": dummy_articles})

# 뉴스 요약 결과 화면
@app.get("/summary", response_class=HTMLResponse)
async def read_summary(request: Request, title: str):
    # OpenAI 붙이기 전이라 임시 요약문 반환
    summary = f"'{title}' 기사의 요약입니다. 실제 요약 기능은 OpenAI API로 연결 예정입니다."
    return templates.TemplateResponse("summary.html", {"request": request, "title": title, "summary": summary})

# 📰 News5_Summarizer

키워드만 입력하면 관련 최신 뉴스 10개[3page 총 30개]를 보여주고,  
클릭 시 **AI(OpenAI API) 기반 간단 요약**을 제공하는 미니 프로젝트입니다.  

---

## 🚀 프로젝트 개요
- **목표**: 방대한 뉴스 기사 속에서 원하는 정보를 빠르게 요약해 제공
- **특징**:  
  1. **HTML 입력창**에서 키워드 검색  
  2. 외부 **뉴스 Open API**를 통해 최신 뉴스 30건 조회  
  3. 사용자가 원하는 기사를 클릭하면 **OpenAI API**로 자동 요약  
  4. 깔끔한 웹 UI를 통해 결과 확인  

---

## 🛠️ 기술 스택
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)  
- **Frontend**: HTML, CSS, JavaScript (Jinja2 템플릿)  
- **API 활용**:  
  - 뉴스 검색: [NewsAPI.org](https://newsapi.org/)  
  - AI 요약: [OpenAI API](https://platform.openai.com/)  
- **Others**: Python `requests`, `openai`, `uvicorn`

---

## 📂 프로젝트 구조
```

News5_Summarizer/
├─ main.py                # FastAPI 서버 실행 진입점
├─ requirements.txt       # 라이브러리 목록
├─ utils/
│    ├─ news_api.py       # 뉴스 API 호출 함수
│    └─ summarize.py      # OpenAI API 요약 함수
├─ templates/
│    ├─ index.html        # 메인 페이지 (검색 입력 + 뉴스 리스트)
│    └─ summary.html      # 요약 결과 페이지
├─ static/
│    ├─ style.css         # 스타일시트
│    └─ script.js         # 사용자 인터랙션 처리
└─ README.md

````

---

## 👥 팀 역할 분담

* **서버 (main.py)** : 조준희
* **API (utils - news_api.py, summarize.py)** : 유민형
* **프론트엔드 (templates, static)** : 전찬혁

---

## 📌 실행 방법

1. 저장소 클론
```bash
git clone https://github.com/USERNAME/News5_Summarizer.git
cd News5_Summarizer
````

2. 가상환경 생성 및 패키지 설치

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 서버 실행

```bash
uvicorn main:app --reload --port 8000
```

4. 브라우저 접속
   👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

"""
외부 뉴스 API (NewsAPI.org) 호출 유틸
- 뉴스 검색/헤드라인 가져오기
- TTL 캐시로 중복 호출 줄이기
- 429/5xx 오류 시 자동 리트라이
- 팀 공통 Article 모델로 정규화
"""

import os, time, hashlib, json, logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple
import requests
from dotenv import load_dotenv   # ← 추가

# .env 자동 로드
load_dotenv()

log = logging.getLogger(__name__)
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# ──────────────────────────────────────────────────────────────
# Article 데이터 모델 (팀 공통 사용)
# ──────────────────────────────────────────────────────────────
@dataclass
class Article:
    title: str
    description: Optional[str]
    url: str
    urlToImage: Optional[str]
    source_name: Optional[str]
    published_at: Optional[str]

    @staticmethod
    def from_newsapi(d: Dict[str, Any]) -> "Article":
        """
        NewsAPI의 응답 JSON → Article 객체 변환
        """
        return Article(
            title=d.get("title") or "",
            description=d.get("description"),
            url=d.get("url") or "",
            urlToImage=d.get("urlToImage"),
            source_name=(d.get("source") or {}).get("name"),
            published_at=d.get("publishedAt"),
        )

# ──────────────────────────────────────────────────────────────
# TTL 캐시 (기본 60초) — 같은 요청 반복 방지
# ──────────────────────────────────────────────────────────────
class _TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._store: Dict[str, Tuple[float, Any]] = {}

    def _now(self): return time.time()

    def get(self, key: str):
        """
        캐시에서 key를 꺼냄 (만료되었으면 제거 후 None 리턴)
        """
        item = self._store.get(key)
        if not item: return None
        ts, val = item
        if self._now() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, val: Any):
        """
        key에 새로운 값 저장
        """
        self._store[key] = (self._now(), val)

_cache = _TTLCache(ttl_seconds=60)

# ──────────────────────────────────────────────────────────────
# 공통 HTTP GET 유틸 (리트라이 포함)
# ──────────────────────────────────────────────────────────────
def _http_get(url: str, params: Dict[str, Any], timeout=12, retries=2) -> Dict[str, Any]:
    """
    - 캐시 먼저 확인
    - 요청 실패(429/5xx) 시 지수 백오프로 재시도
    - 성공 시 JSON 응답 리턴
    """
    raw_key = url + "?" + json.dumps(params, sort_keys=True, ensure_ascii=False)
    key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    cached = _cache.get(key)
    if cached:
        return cached

    backoff = 1.0
    for attempt in range(retries + 1):
        r = requests.get(url, params=params, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            _cache.set(key, data)
            return data

        # 재시도 조건
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
            log.warning("NewsAPI %s, retrying in %.1fs...", r.status_code, backoff)
            time.sleep(backoff); backoff *= 2
            continue

        # 나머지 에러는 즉시 예외
        try: detail = r.json()
        except Exception: detail = r.text
        raise RuntimeError(f"NewsAPI error {r.status_code}: {detail}")

# ──────────────────────────────────────────────────────────────
# 퍼블릭 클라이언트 (팀에서 호출하는 부분)
# ──────────────────────────────────────────────────────────────
class NewsAPIClient:
    BASE = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None, language: str = "ko"):
        self.api_key = api_key or NEWSAPI_KEY
        if not self.api_key:
            raise EnvironmentError("NEWSAPI_KEY 미설정")
        self.default_language = language

    def top_headlines(self, country: Optional[str]=None, category: Optional[str]=None, page_size: int=8) -> List[Article]:
        """
        국가/카테고리 기반 최신 헤드라인 가져오기
        """
        url = f"{self.BASE}/top-headlines"
        params = {"apiKey": self.api_key, "pageSize": page_size}
        if country:  params["country"] = country
        if category: params["category"] = category
        data = _http_get(url, params)
        return [Article.from_newsapi(a) for a in data.get("articles", [])]

    def search(self, query: str, page_size: int=8, sort_by: str="publishedAt", language: Optional[str]=None) -> List[Article]:
        """
        Everything 엔드포인트: 특정 주제로 뉴스 검색
        """
        url = f"{self.BASE}/everything"
        params = {
            "apiKey": self.api_key, "q": query, "pageSize": page_size,
            "sortBy": sort_by, "language": language or self.default_language
        }
        data = _http_get(url, params)
        return [Article.from_newsapi(a) for a in data.get("articles", [])]

# ──────────────────────────────────────────────────────────────
# 단독 실행 테스트
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = NewsAPIClient()
    items = client.search("반도체", page_size=3)
    print([asdict(x) for x in items])


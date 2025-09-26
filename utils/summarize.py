import os, textwrap, logging, requests
from typing import Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup   # ← 추가

# .env 자동 로드
load_dotenv()

log = logging.getLogger(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class Summarizer:
    def __init__(self, model: str="gpt-4o-mini", temperature: float=0.2):
        if not OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY 미설정")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.temperature = temperature

    # ──────────────────────────────
    # URL에서 본문 HTML 추출
    # ──────────────────────────────
    @staticmethod
    def _fetch_article_text(url: str, max_chars: int = 4000) -> str:
        """
        뉴스 URL에서 본문 텍스트 추출
        - <p> 태그 기준으로 긁어오기
        - 너무 길면 앞부분만 자름
        """
        try:
            res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
            text = " ".join(paragraphs).strip()

            if not text:
                return ""
            return text[:max_chars]  # GPT에 넘길 때 길이 제한
        except Exception as e:
            log.warning("본문 추출 실패 (%s): %s", url, e)
            return ""

    # ──────────────────────────────
    # 프롬프트 생성
    # ──────────────────────────────
    @staticmethod
    def _build_prompt(title: str, description: str, url: Optional[str], article_text: Optional[str]) -> str:
        base = f"제목: {title}\n설명: {description or ''}\n원문 URL: {url or ''}\n본문: {article_text or ''}"
        return textwrap.dedent(f"""
        아래 뉴스 기사를 한국어로 **정확히 3줄**로 요약해줘.
        - 각 줄은 핵심 1문장.
        - 수치/날짜/고유명사는 유지.
        - 추측/과장은 금지.

        뉴스:
        {base}
        """)

    # ──────────────────────────────
    # 요약 실행
    # ──────────────────────────────
    def summarize_3lines(self, *, title: str, description: Optional[str]=None, url: Optional[str]=None, fallback: bool=True) -> str:
        article_text = ""
        if url:
            article_text = self._fetch_article_text(url)

        prompt = self._build_prompt(title, description or "", url, article_text)

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            summary = (resp.choices[0].message.content or "").strip()
            return self._postprocess(summary)
        except Exception as e:
            log.exception("OpenAI summarize failed: %s", e)
            if not fallback:
                raise
            # fallback: 기본 정보만 출력
            lines: List[str] = []
            if title:       lines.append(f"① {title.strip()[:140]}")
            if description: lines.append(f"② {description.strip()[:140]}")
            if url:         lines.append(f"③ 자세히 보기: {url}")
            while len(lines) < 3:
                lines.append("· 추가 정보 부족")
            return "\n".join(lines[:3])

    # ──────────────────────────────
    # 후처리: 항상 3줄 맞추기
    # ──────────────────────────────
    @staticmethod
    def _postprocess(text: str) -> str:
        raw = [ln.strip(" -•\t") for ln in text.strip().splitlines() if ln.strip()]
        if len(raw) >= 3:
            return "\n".join(raw[:3])
        joined = " ".join(raw)
        parts = [p.strip() for p in joined.replace("?", ".").split(".") if p.strip()]
        while len(parts) < 3:
            parts.append("추가 정보 없음")
        return "\n".join(parts[:3])

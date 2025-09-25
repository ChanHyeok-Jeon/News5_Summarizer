"""
OpenAI GPT API를 이용한 요약 유틸
- 제목/설명/링크 기반 3줄 요약
- 오류 발생 시 fallback 요약 제공
- 항상 3줄로 맞추도록 후처리
"""

import os, textwrap, logging
from typing import Optional, List
from openai import OpenAI

log = logging.getLogger(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class Summarizer:
    def __init__(self, model: str="gpt-4o-mini", temperature: float=0.2):
        """
        - model: 사용할 GPT 모델 (기본 gpt-4o-mini)
        - temperature: 창의성 정도 (낮을수록 보수적)
        """
        if not OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY 미설정")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        self.temperature = temperature

    # ─────────────────────────────────────────────
    # 프롬프트 생성
    # ─────────────────────────────────────────────
    @staticmethod
    def _build_prompt(title: str, description: str, url: Optional[str]) -> str:
        """
        GPT에 전달할 프롬프트 생성
        - 반드시 3줄로 요약하도록 지시
        """
        base = f"제목: {title}\n설명: {description or ''}\n원문: {url or ''}"
        return textwrap.dedent(f"""
        아래 뉴스 내용을 한국어로 **정확히 3줄**로 요약해줘.
        - 각 줄은 핵심 1문장.
        - 수치/날짜/고유명사는 유지.
        - 추측/과장은 금지.

        뉴스:
        {base}
        """)

    # ─────────────────────────────────────────────
    # 요약 실행 + 예외 시 fallback
    # ─────────────────────────────────────────────
    def summarize_3lines(self, *, title: str, description: Optional[str]=None, url: Optional[str]=None, fallback: bool=True) -> str:
        """
        GPT를 이용한 3줄 요약
        - GPT 호출 실패 시 fallback으로 제목/설명/링크를 단순 출력
        """
        prompt = self._build_prompt(title, description or "", url)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role":"user","content":prompt}],
                temperature=self.temperature,
            )
            summary = (resp.choices[0].message.content or "").strip()
            return self._postprocess(summary)
        except Exception as e:
            log.exception("OpenAI summarize failed: %s", e)
            if not fallback: raise
            # fallback: 기본 정보로 3줄 채우기
            lines: List[str] = []
            if title:       lines.append(f"① {title.strip()[:140]}")
            if description: lines.append(f"② {description.strip()[:140]}")
            if url:         lines.append(f"③ 자세히 보기: {url}")
            while len(lines) < 3: lines.append("· 추가 정보 부족")
            return "\n".join(lines[:3])

    # ─────────────────────────────────────────────
    # 후처리: 항상 3줄 맞추기
    # ─────────────────────────────────────────────
    @staticmethod
    def _postprocess(text: str) -> str:
        """
        모델 출력이 3줄이 아닐 때 → 강제로 3줄로 보정
        """
        raw = [ln.strip(" -•\t") for ln in text.strip().splitlines() if ln.strip()]
        if len(raw) >= 3:
            return "\n".join(raw[:3])
        # 한 줄만 왔을 때: 마침표 기준으로 잘라서 보정
        joined = " ".join(raw)
        parts = [p.strip() for p in joined.replace("?", ".").split(".") if p.strip()]
        while len(parts) < 3: parts.append("추가 정보 없음")
        return "\n".join(parts[:3])

# ──────────────────────────────────────────────────────────────
# 단독 실행 테스트
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = Summarizer()
    print(s.summarize_3lines(
        title="삼성, 차세대 HBM 개발 발표",
        description="HBM4 양산 계획을 공개하며 경쟁력 강화를 예고.",
        url="https://example.com",
    ))

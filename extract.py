"""Solar를 이용한 필드 추출. 크롤 원문 + 시트 셀 → 정확·간결한 항목값(JSON).

핵심 원칙(정확도):
- 제공된 텍스트에 없으면 임의로 채우지 않고 value=null, source="none"
- 어학요건은 "TOEFL 80+, IELTS 6.0+" 형태로 압축
- 수업언어는 영어/현지어/혼합 중 하나
- 해외수학전공은 학부(faculty) 단위 개방여부 요약
"""
import json
import solar
import config

MAX_SOURCE_TEXT = 14000   # 학교당 크롤 텍스트 총 상한

SYSTEM = (
    "너는 교환학생 협정 정보를 웹페이지·팩트시트 원문에서 정확히 추출하는 도우미다. "
    "반드시 제공된 [원문]과 [시트값]에 근거해서만 답한다. 근거가 없으면 절대 지어내지 말고 "
    "value를 null, source를 \"none\"으로 둔다. 출력은 지정한 JSON 스키마만."
)

SCHEMA_GUIDE = """
다음 JSON 스키마로만 답하라(설명 금지):
{
  "gpa_min": {"value": "예: 3.0/4.0 (없으면 null)", "source": "web|factsheet|sheet|none", "evidence": "근거 문구 30자 이내"},
  "language_requirements": {"value": "예: TOEFL iBT 80+, IELTS 6.5+ (없으면 null)", "source": "web|factsheet|sheet|none", "evidence": ""},
  "language_of_instruction": {"value": "영어 또는 현지어 또는 혼합 중 정확히 하나의 단어만(없으면 null)", "source": "web|factsheet|sheet|none", "evidence": ""},
  "major_abroad_summary": {"value": "학부 단위 개방여부 요약. 예: '대부분 학부 개방(경영/공학/인문 등), 의·약·법 제한' (없으면 null)", "source": "web|factsheet|sheet|none", "evidence": ""},
  "campus": {"value": "지원가능 캠퍼스를 사람이 읽기 쉽게 한 줄로 (없으면 null)", "source": "web|sheet|none", "evidence": ""}
}
규칙:
- 어학요건: **주요 시험만 간결히** — TOEFL iBT, IELTS, Duolingo(DET), PTE Academic 위주로 최대 4개까지. ACT/SAT/AP/IB/Cambridge/EIKEN/GTEC/WASSCE/CSEC 등 부수 시험은 제외. 시험명+최소점수만, '+'로 이상 표기, 콤마 구분. 세부영역(subscore)이 아니라 **전체(overall) 점수**를 쓰고, subscore는 넣지 않는다. 홈피 참조만 있고 점수 없으면 value=null.
- language_of_instruction: 반드시 '영어' '현지어' '혼합' 중 **정확히 한 단어**만. '|'로 여러 개 나열 금지. 영어권(미국/영국/호주 등)이면 '영어', 비영어권에서 교환생 대상 영어강의가 상당수면 '혼합', 대부분 현지어면 '현지어'. 근거가 국가뿐이면 evidence에 '영어권' 등으로 적고 source='sheet'.
- 값은 한국어로 간결하게. 시험 점수·고유명사는 원문 유지.
"""


def _sheet_block(sheet):
    keys = [("지원가능캠퍼스(D)", "campus"), ("해외수학전공(F)", "major_abroad"),
            ("최소GPA(N)", "gpa_min"), ("어학요건(J)", "language_req"),
            ("추가정보(X)", "additional")]
    lines = []
    for label, k in keys:
        v = sheet.get(k)
        if v:
            lines.append(f"- {label}: {v}")
    return "\n".join(lines) if lines else "(없음)"


def _sources_block(sources):
    parts, total = [], 0
    for s in sources:
        if not s.get("ok") or not s.get("text"):
            continue
        budget = max(1500, MAX_SOURCE_TEXT // max(1, len(sources)))
        chunk = s["text"][:budget]
        header = f"[원문:{s.get('col')} / {s.get('kind')} / {s['url'][:80]}]"
        parts.append(header + "\n" + chunk)
        total += len(chunk)
        if total >= MAX_SOURCE_TEXT:
            break
    return "\n\n".join(parts) if parts else "(크롤링된 원문 없음 — 접근 차단/링크 없음)"


def extract_fields(rec, sources):
    sheet = rec["sheet"]
    user = (
        f"대학명: {rec['university']}\n국가: {rec['country']}\n\n"
        f"[시트값]\n{_sheet_block(sheet)}\n\n"
        f"[원문]\n{_sources_block(sources)}\n\n"
        f"{SCHEMA_GUIDE}"
    )
    out = solar.chat_json(SYSTEM, user)
    return out

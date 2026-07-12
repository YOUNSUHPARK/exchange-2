"""새 변수 '특징': 교환 지망생에게 유용한 학교 특징 최대 4개.

3계층 알고리즘 (신뢰도 순, 설계 2026-07-12 사용자 승인):
1) 규칙 기반(자동) — 검증된 기존 데이터에서 파생, AI 불개입
2) 근거 기반(시트/웹) — Solar가 시트 추가정보(X)·크롤 원문에서만 추출, 근거 필수
3) 일반 지식(AI추정) — 학교 특성화/위상 1개만, 불확실하면 생략
"""
import re
import solar

MAX_FEATURES = 4
MAX_LEN = 45

SYSTEM = (
    "너는 교환학생 지망생에게 유용한 대학 특징을 추출하는 도우미다. "
    "[시트 추가정보]와 [크롤 원문]에 실제로 적힌 내용만 근거로 쓰고, 근거가 없으면 null. "
    "일반 지식은 knowledge 필드에만, 확실한 경우에만 쓴다. 지정한 JSON 스키마로만 답하라."
)

GUIDE = """
JSON 스키마 (각 값은 한국어 40자 이내 한 구절, 근거 없으면 null):
{
  "housing": {"text": "기숙사 사실 (예: '교환학생 기숙사 보장', '교내 기숙사 미보장·조기신청 필요'), 없으면 null", "evidence": "근거 원문 30자"},
  "support": {"text": "버디/멘토/전담 오리엔테이션 등 교환학생 지원 프로그램, 없으면 null", "evidence": ""},
  "program": {"text": "교환 프로그램 규모·활성도 (예: '연 200명+ 교환학생 수용', '파트너 300개교'), 없으면 null", "evidence": ""},
  "practical": {"text": "학생의 선택에 영향 주는 실용 사실 (교환학생 장학금, 트라이메스터제 등 특이 학사일정, 필수 보험·교통비), 없으면 null", "evidence": ""},
  "knowledge": {"text": "일반 지식 기반 학교 특성 딱 1개, 구체적으로 (예: '공학 특성화', 'QS 최상위권 종합대', '경영 트리플크라운 인증'). '국립대' 같은 무의미한 서술이나 확실하지 않으면 null", "evidence": ""}
}
규칙:
- 원문에 없는 내용을 housing/support/program/practical에 절대 넣지 말 것.
- 지원 절차 요건(서류 제출, 성적 유효기간, 번역본, 어학 증명, 지원 마감 등)은 특징이 아님 — 넣지 말 것.
- 모든 교환에 공통인 것도 특징이 아님: '교환 프로그램 운영', '학비 면제(홈교 납부)',
  '생활 정보 제공' 등은 null. program은 구체적 숫자·규모가 있을 때만.
- GPA·어학요건·수강학점 요건은 별도 항목에 이미 있으므로 특징에 넣지 말 것.
- '정보 없음' 류의 부정 서술을 쓰지 말 것 — 그 경우 null.
- 과장·홍보 문구 금지, 사실만. 각 text는 명사형으로 간결하게.
"""


def rule_features(rec):
    """1계층: 기존 검증 데이터에서 결정적으로 파생 (라벨=자동)."""
    out = []
    loc = rec.get("location", {})
    if loc.get("city_size") == "대도시" and (loc.get("commute_min") or 99) <= 10:
        out.append({"text": "도심 도보권 캠퍼스", "source": "자동"})
    li = rec.get("lang_instruction", {}).get("value", "")
    country = rec.get("country", "")
    eng_native = country in ("UNITED STATES", "UNITED KINGDOM", "AUSTRALIA", "SINGAPORE", "HONG KONG")
    if li == "영어" and not eng_native:
        out.append({"text": "비영어권이지만 전 과정 영어 수업", "source": "자동"})
    lr = rec.get("lang_req", {}).get("value", "")
    if lr.startswith(("SKKU", "공인성적 불요")):
        out.append({"text": "공인 어학성적 없이 지원 가능", "source": "자동"})
    g = rec.get("gpa_min", {}).get("value", "")
    if g.startswith(("제한 없음", "명시 없음")):
        out.append({"text": "GPA 요건 없음", "source": "자동"})
    return out[:2]  # 규칙 기반은 최대 2개


_BAD = ("null", "n/a", "정보 없음", "관련 정보", "정보 제공", "제출", "유효기간",
        "번역본", "해당 시", "마감", "증명 필요", "학비 면제", "등록금 면제",
        "gpa", "ielts", "toefl")
# 공허한 서술: 숫자 없는 '프로그램 운영', '국립/사립 종합대' 단독
_VACUOUS = re.compile(r"(교환\s*(학생)?\s*프로그램\s*(운영|제공)$)|(^[가-힣]{0,4}\s*(국립|사립|공립)?\s*(종합)?대(학교?)?$)")


def _valid_text(t):
    if not isinstance(t, str):
        return False
    t = t.strip()
    if not (4 <= len(t) <= MAX_LEN) or "|" in t:
        return False
    if any(b in t.lower() for b in _BAD):
        return False
    return not _VACUOUS.search(t)


def ai_features(rec, sheet_additional, sources_text):
    """2·3계층: Solar 추출. 반환 [{text, source}]."""
    user = (
        f"대학명: {rec['university']}\n국가: {rec['country']}\n\n"
        f"[시트 추가정보]\n{sheet_additional or '(없음)'}\n\n"
        f"[크롤 원문]\n{sources_text or '(없음)'}\n\n" + GUIDE
    )
    out = solar.chat_json(SYSTEM, user)
    feats = []
    for key, label in (("housing", "웹"), ("support", "웹"),
                       ("program", "웹"), ("practical", "웹"), ("knowledge", "AI추정")):
        o = out.get(key) or {}
        t = (o.get("text") or "").strip() if isinstance(o, dict) else ""
        if not _valid_text(t):
            continue
        # 근거 요구: knowledge 외에는 evidence가 비면 제외
        ev = (o.get("evidence") or "").strip() if isinstance(o, dict) else ""
        if key != "knowledge" and not ev:
            continue
        src = label
        if key != "knowledge" and sheet_additional and not sources_text:
            src = "시트"
        feats.append({"text": re.sub(r"\s+", " ", t), "source": src})
    return feats


def collect(rec, sheet_additional, sources_text):
    feats = rule_features(rec)
    feats += ai_features(rec, sheet_additional, sources_text)
    # 중복 제거 + 상한
    seen, out = set(), []
    for f in feats:
        if f["text"] in seen:
            continue
        seen.add(f["text"])
        out.append(f)
        if len(out) >= MAX_FEATURES:
            break
    return out

"""Solar 기반 위치 추정 → 3단계 분류(도시/준도시/도시 외곽).

Solar는 사실(도시명·도시 규모·도심까지 분)만 추정하고, 분류는 classify_tier가 코드로 판정.
설계: docs/superpowers/specs/2026-07-11-location-tier-design.md (라벨=AI추정, 사용자 승인)
"""
import solar

CITY_SIZES = ("대도시", "소도시", "마을")

SYSTEM = (
    "너는 대학 캠퍼스의 지리적 위치를 아는 도우미다. 캠퍼스 소재 도시와 "
    "도심까지의 대중교통 소요시간을 사실 위주로 추정한다. 과장 없이, 모르면 보수적으로. "
    "지정한 JSON 스키마로만 답하라."
)

GUIDE = """
JSON 스키마 (각 필드는 아래 설명대로 정확히 채울 것):
{
  "city": "캠퍼스가 있는 도시/타운명 (한국어 표기, 예: 나고야)",
  "city_size": "그 도시의 규모. 반드시 다음 세 단어 중 정확히 하나만: 대도시 / 소도시 / 마을
    - 대도시 = 광역권 인구 약 50만 이상이거나 그 나라의 주요 도시
    - 소도시 = 인구 약 5만~50만 (대학도시 포함)
    - 마을 = 인구 5만 미만의 작은 타운·시골",
  "commute_min": 캠퍼스에서 그 도시 도심(중심가/중앙역)까지 대중교통 실제 소요시간(분, 정수).
    캠퍼스가 도심 한복판(도보권)일 때만 10 이하를 쓰고, 그렇지 않으면 반올림하지 말고
    실제 추정치를 그대로 쓸 것. 예: 나고야대는 나고야역에서 지하철 약 20분이므로 20,
  "transport": "주 교통수단 한 단어 (지하철/버스/트램/기차/도보 등)",
  "major_city_min": city_size가 소도시나 마을이면, 캠퍼스에서 가장 가까운 대도시 도심까지
    대중교통 소요시간(분, 정수). 대도시의 통근권 교외 타운이라면 그 대도시 기준
    (예: 보스턴 근교 월섬이면 보스턴까지 약 20분 → 20). 대도시면 null,
  "major_city_note": "city_size가 소도시나 마을이면 그 대도시명과 소요시간 서술 (예: '스톡홀름에서 기차 약 40분'). 대도시면 빈 문자열"
}
규칙: city_size에 여러 값을 나열하거나 '|'를 쓰지 말 것. commute_min은 반드시 숫자 하나.
캠퍼스가 여러 곳이면 교환학생이 가는 대표(메인) 캠퍼스 기준. 소재지를 확실히 모르면 보수적으로 추정.
"""

RETRY_NOTE = (
    "\n\n[교정] 직전 응답이 형식을 어겼다. city_size는 '대도시'/'소도시'/'마을' 중 "
    "정확히 한 단어, commute_min은 정수 하나, city_size가 소도시/마을이면 "
    "major_city_min도 정수 하나여야 한다. 다시 답하라."
)


def _valid(out):
    """Solar 응답 형식 검증. 통과하면 (city_size, commute_min, major_city_min), 아니면 None."""
    size = out.get("city_size")
    if not isinstance(size, str) or size.strip() not in CITY_SIZES:
        return None
    size = size.strip()
    try:
        minutes = int(float(out.get("commute_min")))
    except (TypeError, ValueError):
        return None
    if minutes < 0:
        return None
    major_min = out.get("major_city_min")
    if size == "대도시":
        major_min = None
    else:
        try:
            major_min = int(float(major_min))
        except (TypeError, ValueError):
            return None  # 소도시/마을은 대도시까지 시간이 분류에 필수
        if major_min < 0:
            return None
    return size, minutes, major_min


def classify_tier(city_size, commute_min, major_city_min=None):
    """분류 규칙 (사용자 확정, 2026-07-11 2차 수정):
    소도시/마을 구분 없이 타운 시내(≤30분) 또는 대도시 60분 이내면 준도시.
    도시 외곽은 둘 다 아닌 고립 캠퍼스만."""
    if city_size == "대도시":
        if commute_min <= 10:
            return "도시"
        if commute_min < 60:
            return "준도시"
        return "도시 외곽"
    if major_city_min is not None and major_city_min <= 60:
        return "준도시"  # 대도시 통근권
    if commute_min <= 30:
        return "준도시"  # 대학도시/타운 시내
    return "도시 외곽"


def format_text(tier, city, city_size, commute_min, transport, major_note):
    transport = (transport or "대중교통").strip()
    major_note = (major_note or "").strip()
    if city_size == "대도시":
        if commute_min <= 10:
            desc = f"{city} 도심에 위치"
        else:
            desc = f"{city} 도심까지 {transport} 약 {commute_min}분"
    elif city_size == "소도시":
        if commute_min <= 30:
            desc = f"소도시 {city} 시내"
        else:
            desc = f"소도시 {city} 중심까지 {transport} 약 {commute_min}분"
        if major_note:
            desc += f" ({major_note})"
    else:  # 마을
        desc = f"소도시·마을({city}) 소재"
        if major_note:
            desc += f", {major_note}"
    return f"{tier} — {desc}"


def estimate(university, country, campus_hint=None):
    user = f"대학명: {university}\n국가: {country}\n"
    if campus_hint:
        user += f"캠퍼스 정보: {campus_hint}\n"
    user += "\n" + GUIDE

    out = solar.chat_json(SYSTEM, user)
    ok = _valid(out)
    if ok is None:
        out = solar.chat_json(SYSTEM, user + RETRY_NOTE)
        ok = _valid(out)
    if ok is None:
        return None  # 호출부에서 확인필요 처리

    city_size, commute_min, major_city_min = ok
    city = (out.get("city") or "").strip() or "확인필요"
    transport = out.get("transport", "")
    major_note = out.get("major_city_note", "")
    tier = classify_tier(city_size, commute_min, major_city_min)
    text = format_text(tier, city, city_size, commute_min, transport, major_note)
    return {
        "city": city,
        "city_size": city_size,
        "commute_min": commute_min,
        "major_city_min": major_city_min,
        "transport": (transport or "").strip(),
        "major_city_note": (major_note or "").strip(),
        "tier": tier,
        "setting": tier,  # 하위 호환(기존 필드명)
        "commute": text.split(" — ", 1)[1] if " — " in text else text,
        "text": text,
    }

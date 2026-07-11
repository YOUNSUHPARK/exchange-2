"""Solar 기반 위치 추정: 대학+캠퍼스 → 도시와 '도심에서 대중교통으로 얼마나 떨어졌는지' 서술.

사용자 승인: 정확한 교통 API 없이 AI 추정 서술로 충분(라벨=AI추정).
"""
import solar

SYSTEM = (
    "너는 대학 캠퍼스의 지리적 위치를 아는 도우미다. 캠퍼스가 도시 중심(도심)에서 "
    "대중교통으로 얼마나 떨어져 있는지 한국어로 간결히 서술한다. 과장 없이, 모르면 대략 범위로. "
    "지정한 JSON 스키마로만 답하라."
)

GUIDE = """
JSON 스키마:
{
  "city": "소재 도시",
  "setting": "도심|도심 인접|외곽|교외/소도시 중 하나",
  "commute": "도심에서 대중교통으로 걸리는 정도를 한 줄로. 예: '시내에서 버스/트램 약 15분' 또는 '도심에 위치'",
  "note": "특이사항(캠퍼스가 여러 곳이면 대표 캠퍼스 기준 등, 없으면 빈 문자열)"
}
규칙: 실제로 잘 모르면 commute를 '대략 …분(추정)'처럼 범위로. 도시 자체가 소도시면 그 사실을 setting/commute에 반영.
"""


def estimate(university, country, campus_hint=None):
    user = f"대학명: {university}\n국가: {country}\n"
    if campus_hint:
        user += f"캠퍼스 정보: {campus_hint}\n"
    user += "\n" + GUIDE
    out = solar.chat_json(SYSTEM, user)
    # 한 줄 서술로 합치기
    city = out.get("city") or ""
    setting = out.get("setting") or ""
    commute = out.get("commute") or ""
    text = commute
    if setting and setting not in commute:
        text = f"{commute} ({setting})" if commute else setting
    return {"city": city, "setting": setting, "commute": commute,
            "note": out.get("note", ""), "text": text}

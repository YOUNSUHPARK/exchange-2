"""classify_tier/_valid 경계값 테스트. 실행: python test_location.py"""
from location import classify_tier, _valid, format_text

CASES = [
    # (city_size, commute_min, major_city_min, expected)
    ("대도시", 0, None, "도시"),
    ("대도시", 10, None, "도시"),
    ("대도시", 11, None, "준도시"),
    ("대도시", 20, None, "준도시"),   # 나고야대 사례
    ("대도시", 59, None, "준도시"),
    ("대도시", 60, None, "도시 외곽"),
    ("대도시", 120, None, "도시 외곽"),
    ("소도시", 0, 240, "준도시"),     # 고립된 대학도시 시내 (사용자 확정)
    ("소도시", 30, 240, "준도시"),
    ("소도시", 31, 240, "도시 외곽"),
    ("소도시", 45, 40, "준도시"),     # 대도시 통근권 교외
    ("마을", 0, 20, "준도시"),        # Brandeis(월섬): 보스턴 20분 → 준도시
    ("마을", 0, 59, "준도시"),
    ("마을", 0, 60, "도시 외곽"),
    ("마을", 0, 240, "도시 외곽"),    # Wyoming(라라미): 덴버 2.5시간
    ("마을", 0, None, "도시 외곽"),
]

for size, minutes, major, expected in CASES:
    got = classify_tier(size, minutes, major)
    assert got == expected, f"classify_tier({size!r}, {minutes}, {major}) = {got!r}, 기대 {expected!r}"

# _valid: 형식 위반 거부
assert _valid({"city_size": "대도시", "commute_min": 20}) == ("대도시", 20, None)
assert _valid({"city_size": "대도시", "commute_min": "20", "major_city_min": 50}) == ("대도시", 20, None)
assert _valid({"city_size": " 소도시 ", "commute_min": 15.0, "major_city_min": "40"}) == ("소도시", 15, 40)
assert _valid({"city_size": "마을", "commute_min": 0, "major_city_min": 90}) == ("마을", 0, 90)
assert _valid({"city_size": "소도시", "commute_min": 15}) is None            # major_city_min 누락
assert _valid({"city_size": "마을", "commute_min": 0, "major_city_min": None}) is None
assert _valid({"city_size": "대도시|소도시", "commute_min": 20}) is None
assert _valid({"city_size": "도심", "commute_min": 20}) is None
assert _valid({"city_size": "대도시", "commute_min": "약 20분"}) is None
assert _valid({"city_size": "대도시", "commute_min": None}) is None
assert _valid({"city_size": "대도시", "commute_min": -5}) is None

# format_text 대표 사례
assert format_text("준도시", "나고야", "대도시", 20, "지하철", "") == "준도시 — 나고야 도심까지 지하철 약 20분"
assert format_text("도시", "멜버른", "대도시", 0, "도보", "") == "도시 — 멜버른 도심에 위치"
assert format_text("준도시", "웁살라", "소도시", 5, "버스", "스톡홀름에서 기차 약 40분") == \
    "준도시 — 소도시 웁살라 시내 (스톡홀름에서 기차 약 40분)"

print("test_location.py: 모든 테스트 통과")

"""이메일문의/확인필요 미확보값 채우기 1차 (2026-07-13, 공식 페이지·factsheet 확인분만).

원칙: 인바운드(교환 수용) 요건이 공식 자료로 확인된 값만 기입 (source=웹).
아웃바운드 요건·애그리게이터 수치·파트너별 상이 값은 채우지 않고 이메일문의 유지.
실행 후: python build_table.py && python build_site.py
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# (대학명, 필드) → 값
FILL = {
    ("University of British Columbia(UBC)", "gpa_min"): "3.0/4.0 (B 또는 70%)",
    ("University of British Columbia(UBC)", "credits_min"): "명시 없음 (통상 9~15 credits)",
    ("University of British Columbia(UBC)", "credits_max"): "15 credits",
    ("University of British Columbia(UBC)", "lang_req"):
        "TOEFL iBT 90점 이상 또는 IELTS 6.5점 이상 (밴드 6.0) 또는 Duolingo 125점 이상 또는 PTE 65점 이상 (협정에 따라 면제 가능)",
    ("Universite du Quebec a Montreal(UQAM)", "gpa_min"): "명시 없음",
    ("Universite du Quebec a Montreal(UQAM)", "credits_min"): "12 credits (학부; 대학원 6)",
    ("Universite du Quebec a Montreal(UQAM)", "credits_max"): "15 credits (학부; 대학원 9)",
    ("Universite du Quebec a Montreal(UQAM)", "lang_req"): "프랑스어 CEFR B2 이상",
    ("Roskilde University", "lang_req"): "영어 CEFR B2 (증빙 필요)",
    ("Roskilde University", "credits_min"): "30 ECTS (풀타임 기준)",
    ("Roskilde University", "credits_max"): "30 ECTS",
    ("Roskilde University", "semesters"): "2학기 이상 (60 ECTS)",
    ("Kyoto University", "lang_req"):
        "TOEFL iBT 72점 이상 (신척도 4) 또는 IELTS 6.5점 이상 (KUINEP 기준)",
    ("Kyoto University", "credits_min"): "7과목 (KUINEP·GEA 학부; 대학원 4과목)",
    ("Kyoto University", "credits_max"): "명시 없음",
    ("Boise State University", "credits_min"): "12 US credits",
    ("Boise State University", "credits_max"): "15 US credits (초과 시 추가 비용)",
    ("University of Toronto", "gpa_min"): "2.7/4.0 (학부; 대학원 3.0/4.0)",
    ("University of Toronto", "credits_max"): "2.5 UofT credits (5과목, 풀타임)",
    ("Rennes School of Business", "gpa_min"): "3.0/4.0",
    ("Rennes School of Business", "credits_min"): "명시 없음 (표준 30 ECTS)",
    ("Rennes School of Business", "credits_max"): "30 ECTS (표준)",
    ("Bogazici University", "gpa_min"): "명시 없음",
    ("Bogazici University", "lang_req"):
        "TOEFL iBT 79점 이상 (TWE 24) 또는 홈교 B2 확인서 (IELTS 인정)",
    ("Bogazici University", "credits_max"): "명시 없음 (통상 4~6과목)",
    ("University of Bergen", "credits_max"): "제한 없음 (통상 30 ECTS)",
    ("Turku University of Applied Sciences", "lang_req"): "공인성적 불요 (영어 B2 수준 기대)",
    ("Simon Fraser University", "gpa_min"): "제한 없음 (홈교 선발 신뢰)",
    ("Simon Fraser University", "lang_req"):
        "IELTS 6.5점 이상 (밴드 6.0) 또는 영어매체 재학 증명 인정",
    ("Shinshu University", "lang_req"): "명시 없음 (일본어 배치시험; 전공과목은 일본어 필요)",
    ("The Australian National University", "credits_min"): "18 units (감축 승인 시; 표준 24)",
    ("The Australian National University", "credits_max"): "24 units",
    ("The University of Texas at Austin", "gpa_min"): "명시 없음 (Good standing, 프로그램별 상이)",
    ("University of the Sunshine Coast", "gpa_min"): "제한 없음 (홈교 기준 적용)",
    ("Polytechnic University of Milan", "credits_min"): "명시 없음 (통상 30 ECTS)",
    ("Polytechnic University of Milan", "credits_max"): "명시 없음 (통상 30 ECTS)",
    ("Hacettepe University", "credits_min"): "30 ECTS (표준 부하)",
    ("Hacettepe University", "credits_max"): "30 ECTS (표준 부하)",
}


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)
    by_name = {r["university"]: r for r in data}
    n = 0
    for (uni, field), val in FILL.items():
        rec = by_name.get(uni)
        if rec is None:
            print(f"!! 못 찾음: {uni}")
            continue
        g = rec[field]
        old = g.get("value") if isinstance(g, dict) else g
        rec[field] = {"value": val, "source": "웹"}
        print(f"  {uni} [{field}]: {str(old)[:40]!r} → {val[:60]!r}")
        n += 1
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"\n적용 {n}건")


if __name__ == "__main__":
    main()

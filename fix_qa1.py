"""품질조사(2026-07-12) 결과 반영: 표본·패턴 검증에서 확인된 오류 수정.

패턴: 비영어권 대학의 수업언어 '영어' 단독 오판 12곳 → 공식 확인 후 '현지어, 영어' 병기.
개별: ISC 어학(현행 factsheet 80/6.5/785/DET90), 매니토바 어학(현행 86), UTS 완료학기 충원.
근거: 각 대학 공식 페이지/factsheet (세션 기록 참조). ZHAW 학점 등 오탐은 수정하지 않음.
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

LANG_FIX = {  # 대학명 → 수업언어
    "Shandong University": "중국어, 영어",
    "ISC Paris Group": "프랑스어, 영어",
    "Free University of Brussels (ULB)": "프랑스어, 영어",
    "University of Liege": "프랑스어, 영어",
    "KU Leuven": "네덜란드어, 영어",
    "Kyoto University": "일본어, 영어",
    "Soka University": "일본어, 영어",
    "University of Indonesia": "인도네시아어, 영어",
    "University of Cologne": "독일어, 영어",
    "Ca' Foscari University of Venice": "이탈리아어, 영어",
    "Universidad San Francisco de Quito": "스페인어, 영어",
    "University of Zagreb": "크로아티아어, 영어",
}
FIELD_FIX = {  # (대학명, 필드) → 값
    ("ISC Paris Group", "lang_req"):
        "TOEFL iBT 80점 이상 또는 IELTS 6.5점 이상 또는 TOEIC 785점 이상 또는 Duolingo 90점 이상",
    ("University of Manitoba", "lang_req"):
        "IELTS 6.5점 이상 또는 TOEFL iBT 86점 이상 (영역별 20) 또는 CAEL 60점 이상",
    ("University of Technology Sydney", "semesters"):
        "2학기 이상 (1년/60 ECTS 완료)",
}


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)
    n = 0
    for rec in data:
        u = rec["university"]
        if u in LANG_FIX:
            old = rec["lang_instruction"]["value"]
            rec["lang_instruction"] = {"value": LANG_FIX[u], "source": "웹"}
            print(f"  [수업언어] {u}: {old} → {LANG_FIX[u]}")
            n += 1
        for (uu, field), val in FIELD_FIX.items():
            if u == uu:
                old = rec[field]["value"] if isinstance(rec[field], dict) else rec[field]
                rec[field] = {"value": val, "source": "웹"}
                print(f"  [{field}] {u}: {str(old)[:50]} → {val[:60]}")
                n += 1
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"\n적용 {n}건")


if __name__ == "__main__":
    main()

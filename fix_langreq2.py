"""어학요건 2차: PENDING 23곳 확정 적용 (2026-07-12, 사용자 승인 + 공식 페이지 확인).

근거 요약:
- TOEIC 초과 2곳은 오류 아님: 리옹3=4기능 합산 1020, 도요=L&R+S&W×2.5 환산 1530
- TOEFL iBT 'N점 (신척도)' = 2026-01-21부터 적용된 1~6점 새 척도
실행 후: python build_table.py && python build_site.py
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 대학명 → (값, 출처라벨 또는 None=유지)
FINAL = {
    "The University of Melbourne":
        ("IELTS 6.5점 이상 (전 밴드 6.0) 또는 TOEFL iBT 79점 이상", "웹"),
    "University of Newcastle":
        ("IELTS 6.0점 이상 (전 밴드 6.0) 또는 TOEFL iBT 64점 이상 또는 Duolingo 110점 이상 또는 PTE 50점 이상 (학부 기준)", "웹"),
    "Queensland University of Technology":
        ("IELTS 6.5점 이상 (전 밴드 6.0) 또는 TOEFL iBT 79점 이상", "웹"),
    "Toronto Metropolitan University":
        ("IELTS 6.5점 이상 또는 TOEFL iBT 92점 이상 또는 MELAB 90점 이상 또는 PTE 60점 이상", None),
    "Memorial University of Newfoundland":
        ("IELTS 6.5점 이상 (R·W 6.0) 또는 TOEFL iBT 4.5점 이상 (신척도) 또는 Duolingo 115점 이상 또는 PTE 60점 이상", "웹"),
    "University of Copenhagen":
        ("일부 학과만 요구 (TOEFL iBT 83점 또는 신척도 4.5 또는 B2 확인; 그 외 불요)", "웹"),
    "Aalborg University": ("영어 CEFR B2 이상", "웹"),
    "Jean Moulin University Lyon 3":
        ("TOEFL iBT 80점 이상 또는 IELTS 6.5점 이상 또는 TOEIC 1020점 이상 (4기능 합산) 또는 Duolingo 125점 이상", "웹"),
    "Paris 1 Pantheon-Sorbonne University":
        ("프랑스어 CEFR B2 이상 (DELF/DALF/TCF 또는 홈교 교원 확인서)", "웹"),
    "ECE Paris":
        ("IELTS 6.0점 이상 또는 TOEFL iBT 83점 이상 또는 TOEIC 780점 이상 (영어과정); 프랑스어과정은 CEFR B2", "웹"),
    "Ruhr University of Bochum":
        ("학과별 상이 (통상 영어 CEFR B2 — TOEFL iBT 72점·IELTS 5.5점 상당)", "웹"),
    "Leuphana University Luneburg":
        ("영어 CEFR B2 이상 (TOEFL iBT 72점·IELTS 5.0점·TOEIC L&R 785점 상당)", "웹"),
    "Ludwig Maximilian University of Munich":
        ("독일어 CEFR B2 이상 (지원 시 B1); 영어강의만 수강 시 독일어 증명 불요", "웹"),
    "Toyo University":
        ("TOEFL iBT 72점 이상 또는 IELTS 5.5점 이상 또는 TOEIC 1530점 이상 (L&R+S&W×2.5 환산) 또는 JLPT N3 이상", "웹"),
    "Maastricht University":
        ("학부별 상이 (MSP는 TOEFL iBT 90점 이상 등, UCM은 웹사이트 참조)", None),
    "Nanyang Technological University (NTU)":
        ("IELTS 6.0점 이상 (Writing 6.0) 또는 TOEFL iBT 90점 이상 (홈교 확인서 대체 가능)", "웹"),
    "Istanbul Technical University": ("SKKU 어학확인서 인정", None),
    "University of Leicester": ("IELTS 6.5점 이상 (일부 과목 6.0)", None),
    "University of Essex":
        ("IELTS 6.0점 이상 (전 밴드 5.5, 학부) 또는 TOEFL iBT 88점 이상", "웹"),
    "University at Albany, State University of New York(SUNY)":
        ("TOEFL iBT 79점 이상 또는 IELTS 6.5점 이상 또는 PTE 53점 이상", "웹"),
    "Clarkson University":
        ("TOEFL iBT 80점 이상 또는 IELTS 6.5점 이상 (English Ability Form 대체 가능)", "웹"),
    "Washington State University":
        ("IELTS 6.5점 이상 또는 TOEFL iBT 4점 이상 (2026년 신척도 1~6) 또는 Duolingo 105점 이상", None),
    "The Pennsylvania State University":
        ("TOEFL iBT 80점 이상 (신척도 4.5) 또는 IELTS 6.5점 이상 또는 Duolingo 120점 이상", "웹"),
}


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    n = 0
    for rec in data:
        if rec["university"] not in FINAL:
            continue
        val, src = FINAL[rec["university"]]
        g = rec["lang_req"]
        print(f"  {rec['university']}: {str(g.get('value'))[:60]!r} → {val!r}")
        g["value"] = val
        if src:
            g["source"] = src
        n += 1

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"\n적용 {n}건 / 대상 {len(FINAL)}곳")


if __name__ == "__main__":
    main()

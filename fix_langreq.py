"""어학요건을 '시험명 N점 이상 또는 …' 형식으로 통일 (2026-07-12).

- "TOEFL iBT 79+, IELTS 6.5+" → "TOEFL iBT 79점 이상 또는 IELTS 6.5점 이상"
- CEFR/JLPT 등 등급형은 '… B2 이상'/'JLPT N2 이상'
- 공인성적 불요·SKKU 확인서 인정·명시 없음 계열은 한글 표준 문구로
- PENDING(오류/URL만/의심값 학교)은 사용자 결정 전까지 건드리지 않음
실행 후: python build_table.py && python build_site.py
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

KEEP = ("담당자 이메일 문의",)

# 오류/의심/URL만 — 사용자 결정 대기 (2차에서 처리)
PENDING = {
    "The University of Melbourne", "University of Newcastle",
    "Queensland University of Technology", "Toronto Metropolitan University",
    "Memorial University of Newfoundland", "University of Copenhagen",
    "Aalborg University", "Jean Moulin University Lyon 3",
    "Paris 1 Pantheon-Sorbonne University", "ECE Paris",
    "Ruhr University of Bochum", "Leuphana University Luneburg",
    "Ludwig Maximilian University of Munich", "Toyo University",
    "Maastricht University", "Nanyang Technological University (NTU)",
    "Istanbul Technical University", "University of Leicester",
    "University of Essex", "University at Albany, State University of New York(SUNY)",
    "Clarkson University", "Washington State University",
    "The Pennsylvania State University",
}

# 등급/문구형 정확 매핑 (원문 그대로 키)
VALUE_MAP = {
    "N/A": "명시 없음", "n/a": "명시 없음", "NA": "명시 없음",
    "N/A: CEFR B2 level English recommended": "명시 없음 (영어 B2 권장)",
    "N/A Home university is expected to check that the student meets the CEFR B2 level":
        "공인성적 불요 (홈교가 B2 확인)",
    "N/A. We trust our partners to nominate students with sufficient English level to follow the classes.":
        "공인성적 불요",
    "N/A (As long as student is capable of taking courses/research fully delivered in English)":
        "공인성적 불요 (영어 수강 가능 수준)",
    "There's no language certificate requirement.": "공인성적 불요",
    "We expect students to have a minimum of B2 English level. No official language test required.":
        "공인성적 불요 (영어 B2 기대)",
    "B2 level in English is strongly recommended but no language certificate needs to b provided":
        "공인성적 불요 (영어 B2 강력 권장)",
    "No requirements but we recommend having a B2 in english": "공인성적 불요 (영어 B2 권장)",
    "Differs per programme": "프로그램별 상이",
    "B2 level": "영어 CEFR B2 이상", "CEFR B2+": "영어 CEFR B2 이상",
    "CEFR B2": "영어 CEFR B2 이상", "English B2": "영어 CEFR B2 이상",
    "Min B2": "영어 CEFR B2 이상", "B2 (CEFR) in English.": "영어 CEFR B2 이상",
    "English B2 according to CEFR": "영어 CEFR B2 이상",
    "English Level B2 according to CEFR": "영어 CEFR B2 이상",
    "B2 level (certificate or university letter)": "영어 CEFR B2 이상 (홈교 확인서 가능)",
    "B2 CEFR equivalent (Official test or home university certificate)":
        "영어 CEFR B2 이상 (홈교 확인서 가능)",
    "English B1+": "영어 CEFR B1 이상",
    "B1 level German": "독일어 CEFR B1 이상",
    "Spanish B2": "스페인어 CEFR B2 이상",
    "Spanish or English B2 level": "스페인어 또는 영어 CEFR B2 이상",
    "Turkish or English (Minimum B2)": "터키어 또는 영어 CEFR B2 이상",
    "French B1/B2 or English B1/B2": "프랑스어 또는 영어 CEFR B1~B2",
    "B1 level in the language of instruction": "수업언어 CEFR B1 이상",
    "B2 French, B2 English (English Studies)": "프랑스어 CEFR B2 이상 (영문학 전공은 영어 B2)",
    "B2 English, B1 French (if courses in French)":
        "영어 CEFR B2 이상 (프랑스어 수업 수강 시 프랑스어 B1)",
    "IELTS 6.0+, French B2+": "IELTS 6.0점 이상, 프랑스어 CEFR B2 이상",
    "English or German (level B2)- we will not ask \n students to submit certificates.":
        "영어 또는 독일어 CEFR B2 (증빙 불요)",
    "CEFR B2 or equivalent in the language of instruction. For German Studies: German CEFR C1":
        "수업언어 CEFR B2 이상 (독문학은 독일어 C1)",
    "CEFR B1.1 in English or German": "영어 또는 독일어 CEFR B1 이상",
    "CEFR B1 or B2 in English or CEFR B1 in German": "영어 CEFR B1~B2 또는 독일어 B1",
    "German B1/B2 (Human Medicine, Dentistry, Medical Biotechnology: B2), English B1 (CEFR)":
        "독일어 CEFR B1 이상·영어 B1 이상 (의학계열은 독일어 B2)",
    "German B1+, English B1+; Medicine/German Philology: German B2+; Biology: German C1+; Pharmacy: German B2+; Master Medical Life Sciences: English C1+":
        "독일어·영어 CEFR B1 이상 (일부 학과 B2~C1)",
    "Undergraduate: English B1 and/or German B2; Graduate: English B2 and/or German B2":
        "학부: 영어 B1·독일어 B2 이상 / 대학원: 영어 B2·독일어 B2 이상",
    "공식 영어 능력 증명 (B2 이상 학사, C1 이상 석사)": "영어 CEFR B2 이상 (석사 C1)",
    "B2 (General courses), C1 (English language and literature)":
        "영어 CEFR B2 이상 (영문학 전공 C1)",
    "B1 level in Italian Language+, B1 level in English Language+":
        "이탈리아어 또는 영어 CEFR B1 이상",
    "The expected language proficiency level is B2+ (Common European Framework of Reference for Languages). Official confirma":
        "영어 CEFR B2 이상",
    "Students are expected to manage at least a B2 level on the Common European Framework of Reference for Languages. A langu":
        "영어 CEFR B2 이상",
    "Students are expected to arrive with a sufficient level of English in order to be able to follow classes and submit all":
        "공인성적 불요 (수강 가능 수준)",
    "SKKU Letter of proficiency": "SKKU 어학확인서 인정",
    "SKKU Letter of Proficiency": "SKKU 어학확인서 인정",
    "Letter of proficiency (min. B1)": "SKKU 어학확인서 인정 (B1 이상)",
    "B2 - Letter of proficiency issued by the Office of International Relations SKKU":
        "SKKU 어학확인서 인정 (B2 이상)",
    "Letter of proficiency issued by the Office of International Relations SKKU":
        "SKKU 어학확인서 인정",
    "We accept Letter of proficiency issued by the Office of International Relations SKKU":
        "SKKU 어학확인서 인정",
    "Attestation of English Proficiency": "영어능력 증명 제출 (형식 자유)",
    "Please check our fact sheet": "확인필요",
    "TOEFL, IELTS": None,  # PENDING(보훔)이라 실제 사용 안 됨
    "IELTS Academic/for UKVI/Online 6.0+, TOEFL iBT 95+":
        "IELTS 6.0점 이상 (Academic/UKVI/Online) 또는 TOEFL iBT 95점 이상",
    "Bachelor: IELTS 6.0+, TOEFL iBT 80+; Master: IELTS 6.5+, TOEFL iBT 95+":
        "학부: IELTS 6.0점 또는 TOEFL iBT 80점 이상 / 석사: IELTS 6.5점 또는 TOEFL iBT 95점 이상",
    "IELTS 5.0+, TOEFL iBT 60+ (Bachelor), IELTS 6.5+, TOEFL iBT 90+ (Master)":
        "학부: IELTS 5.0점 또는 TOEFL iBT 60점 이상 / 석사: IELTS 6.5점 또는 TOEFL iBT 90점 이상",
    "School of Business and Economics: null, Univeristy College Maastricht: see website, Maastricht Science Programme: TOEFL iBT 90+, TOEFL PBT 575+, TOEFL":
        None,  # PENDING(마스트리흐트)
    "TOEFL iBT ≥80, IELTS ≥6.0, HSK 4 ≥180 (Science/Engineering/Medicine), HSK 5 ≥180 (Economics/Management/Literature/Education/Philosophy/Arts/Law)":
        "TOEFL iBT 80점 이상 또는 IELTS 6.0점 이상 또는 HSK 4급 180점 이상 (이공·의학) / HSK 5급 180점 (인문·사회)",
    "New HSK-5+ (Chinese), TOEFL iBT 80+, IELTS 6.0+":
        "TOEFL iBT 80점 이상 또는 IELTS 6.0점 이상 또는 HSK 5급 이상",
    "New HSK 180+, TOEFL iBT 80+, IELTS 6.0+":
        "TOEFL iBT 80점 이상 또는 IELTS 6.0점 이상 또는 HSK 180점 이상",
    "TOEFL 500PBT+, TOEFL 61iBT+, IELTS 5.5+":
        "TOEFL PBT 500점 이상 또는 TOEFL iBT 61점 이상 또는 IELTS 5.5점 이상",
    "TOEFL iBT 71+, IELTS 6.0+, CET 4.0+ (학부), CET 6.0+ (대학원)":
        "TOEFL iBT 71점 이상 또는 IELTS 6.0점 이상 또는 CET-4 (학부)/CET-6 (대학원)",
    "Cambridge B2 First 180+, C1 Advanced/C2 Proficiency A/B/C, IELTS 6.5+, TOEFL iBT 90+, PTE Academic 62+":
        "IELTS 6.5점 이상 또는 TOEFL iBT 90점 이상 또는 PTE Academic 62점 이상 또는 Cambridge B2 First 180점 이상",
    "TOEFL iBT 90+, IELTS 6.5+, Cambridge English C1 Advanced 180+ or C2 Proficiency":
        "TOEFL iBT 90점 이상 또는 IELTS 6.5점 이상 또는 Cambridge C1 Advanced 180점 이상",
    "DELF/DALF B1+ (Language and Civilisation), DELF/DALF C1+ (Professional Track), JLPT N3 (Japanese 2nd year), JLPT N2 (Japanese 3rd year)":
        "DELF/DALF B1 이상 (언어·문명과정) / C1 (전문과정), JLPT N2~N3 (일본어 전공)",
    "JLPT N2+ (Undergraduate Course), JLPT N4/N3 (Japanese Language and Culture Course)":
        "JLPT N2 이상 (학부 과정) / N4~N3 (일본어·문화 과정)",
    "IELTS 6.0+ (no band below 5.5)": "IELTS 6.0점 이상 (전 밴드 5.5 이상)",
    "확인필요(링크 참조)": None,  # PENDING(올버니)
    "yes we accept your proficiency letter,": None,  # PENDING(ITU)
    "IELTS 6.5+, TOEFL iBT 80+, PTE Academic 64+, Cambridge C1 Advanced":
        "IELTS 6.5점 이상 또는 TOEFL iBT 80점 이상 또는 PTE Academic 64점 이상 또는 Cambridge C1 Advanced",
    "TOEFL iBT 80+, TOEIC 850, IELTS 6.5+, Duolingo 115":
        "TOEFL iBT 80점 이상 또는 TOEIC 850점 이상 또는 IELTS 6.5점 이상 또는 Duolingo 115점 이상",
    "English or German (level B2)- we will not ask students to submit certificates.":
        "영어 또는 독일어 CEFR B2 (증빙 불요)",
    "TOEFL iBT 83+, IELTS 6.5+, B2 level":
        "TOEFL iBT 83점 이상 또는 IELTS 6.5점 이상 (CEFR B2 상당)",
    "B1 English or German": "영어 또는 독일어 CEFR B1 이상",
    "TOEFL IBT 90+, IELTS 7.0+, PTE Academic":
        "TOEFL iBT 90점 이상 또는 IELTS 7.0점 이상 또는 PTE Academic",
    "English B2/C1, German B2": "영어 CEFR B2~C1·독일어 B2 이상",
    "N/A, but at least a B2 English level is strongly recommended":
        "명시 없음 (영어 B2 강력 권장)",
}
VALUE_MAP = {k: v for k, v in VALUE_MAP.items() if v}

TOKEN_PATTERNS = [
    (re.compile(r"(?i)^JLPT\s*(N[1-5])\+?$"), lambda m: f"JLPT {m.group(1).upper()} 이상"),
    (re.compile(r"(?i)^(CEFR\s*)?([ABC][12])\+?$"), lambda m: f"CEFR {m.group(2).upper()} 이상"),
    (re.compile(r"^(.+?[A-Za-z가-힣])\s*([ABC][12])\+$"), lambda m: f"{m.group(1)} {m.group(2)} 이상"),
    (re.compile(r"^(.+?)\s+C\+$"), lambda m: f"{m.group(1)} C 이상"),
    (re.compile(r"^(.+?)\s*(\d+(?:\.\d+)?)\s*\+$"), lambda m: f"{m.group(1)} {m.group(2)}점 이상"),
]


def conv_token(tok):
    tok = tok.strip()
    paren = ""
    m = re.match(r"^(.*?)\s*(\([^()]*\))$", tok)
    if m:
        tok, paren = m.group(1).strip(), " " + m.group(2)
    for pat, fmt in TOKEN_PATTERNS:
        mm = pat.match(tok)
        if mm:
            return fmt(mm) + paren
    return None


def normalize(v):
    v = re.sub(r"\s+", " ", str(v)).strip()
    if not v:
        return "확인필요"
    if v in KEEP or v == "확인필요":
        return v
    if v in VALUE_MAP:
        return VALUE_MAP[v]
    if ("이상" in v or "CEFR" in v or "상이" in v or "증명" in v
            or v.startswith(("명시 없음", "공인성적 불요", "SKKU", "학부:"))):
        return v  # 이미 정리됨
    # 콤마 구분 점수 나열 — 모든 토큰이 변환될 때만 적용
    toks = re.split(r",\s*(?![^()]*\))", v)
    out = [conv_token(t) for t in toks]
    if all(out):
        return " 또는 ".join(out)
    return None


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    n, left = 0, []
    for rec in data:
        if rec["university"] in PENDING:
            continue
        g = rec["lang_req"]
        v = str(g.get("value") or "").strip()
        new = normalize(v)
        if new is None:
            left.append((rec["university"], v))
        elif new != v:
            g["value"] = new
            n += 1

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"변환 {n}건, 미변환 {len(left)}건 (PENDING {len(PENDING)}곳 제외)")
    for u, v in left:
        print(f"  {u}: {v[:120]!r}")


if __name__ == "__main__":
    main()

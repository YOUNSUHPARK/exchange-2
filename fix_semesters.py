"""완료 학기 수를 'N학기 이상' 형식으로 통일 (2026-07-12).

- 'N학기'/'최소 N학기' → 'N학기 이상'
- 원본 시트 'None'/'No requirements' 류 → '제한 없음', N/A 류 → '명시 없음'
- 학부/대학원 구분·60 ECTS(=1년) 오파싱 등은 시트 원문 기준으로 MANUAL 확정
- 오류값(주제와 무관한 내용): UTS·남덴마크대·도요대 → 확인필요
실행 후: python build_table.py && python build_site.py
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

KEEP = ("담당자 이메일 문의", "확인필요")

# 시트 원문(loader로 확인) 기준 확정값
MANUAL = {
    "University of Technology Sydney": "확인필요",  # 시트에 교환 정원 정보만 기재
    "University of Southern Denmark": "확인필요",   # 시트에 수강 학점(30~35 ECTS) 정보만 기재
    "Toyo University": "확인필요",                   # URL만, 페이지에 완료학기 요건 없음
    "MCI Management Center Innsbruck": "4학기 이상 (학부) / 2학기 (대학원)",
    "University of Montreal": "2학기 이상 (학부) / 1학기 (대학원)",
    "Shanghai Jiao Tong University": "2학기 이상 (학부) / 1학기 (대학원)",
    "Vytautas Magnus University": "2학기 이상 (학부) / 1학기 (대학원)",
    "Aalborg University": "4학기 이상 (학부) / 6학기 (대학원)",
    "Osnabruck University of Applied Sciences": "제한 없음 (학부; 대학원 4학기)",
    "Hanken School of Economics": "2학기 이상",       # '2 semesters (1 year)'
    "Tampere University": "2학기 이상",               # 'Two'
    "Haaga-Helia University of Applied Sciences": "2학기 이상",
    "EDHEC Business School": "2학기 이상",            # 'minimum 1 year (2 semesters)'
    "Toulouse Business School": "2학기 이상 (학사과정; 석사는 6학기)",
    "Kiel University": "4학기 이상",                  # 교환학기가 5번째 학기가 되도록
    "Radboud University": "명시 없음 (법·경영 과목은 60 ECTS 이수 필요)",
    "Maastricht University": "2학기 이상 (SBE 기준, 60 ECTS)",
    "University of Bergen": "2학기 이상 (60 ECTS)",
    "Halmstad University": "2학기 이상 (1년)",
    "University of Applied Sciences and Arts Northwestern Switzerland": "2학기 이상 (60 ECTS)",
    "University of Exeter": "4학기 이상 (2년)",
    "University of Bristol": "2학기 이상 (1년)",
    "University of Central Lancashire": "과목 수준별 상이",
    "Tohoku University": "프로그램별 상이 (JYPE 4학기·IPLA 2학기 이상)",
    "ECE Paris": "프로그램별 상이",
    "Linnaeus University": "과정별 상이",
    "Paris School of Urban Engineering (EIVP)": "4~6학기 이상 (프로그램별)",
    "Okanagan College": "1~2학기 이상",
    "University of Illinois Springfield": "1~2학기 이상",
    "Clarkson University": "3~4학기 이상",
    "Linkoping University": "명시 없음 (권장 2~4학기)",
    "University of South Florida": "명시 없음 (권장 2~3학기)",
    "York St John University": "명시 없음 (권장 1학기)",
    "LUT University (Lappeenranta-Lahti University of Technology)": "제한 없음 (권장 2학기)",
    "Nagoya University": "제한 없음 (성적표 제출만)",
    "Tilburg University": "3학기 이상 (권장 4학기)",
    "Frankfurt School of Finance and Management": "4학기 이상 (학부, 경영·경제 전공)",
    "CBS International Business School": "2학기 이상 (경영·IT·공학 관련 전공)",
    "ZHAW Zurich University of Applied Sciences": "2학기 이상 (학사과정)",
    "Hong Kong Polytechnic University": "2학기 이상 (1년)",
    "Ritsumeikan University": "2학기 이상 (1년)",
    "Erasmus University Rotterdam": "2학기 이상 (1년)",
    "Esade Business School": "2학기 이상 (1년)",
    "Huazhong University of Science and Technology": "1학기 이상",
    "National Taiwan University": "1학기 이상",
    "University of Sao Paulo": "홈교 기준",
    "Grenoble Alpes University": "홈교 기준",
    "Arizona State University": "홈교 기준",
    "NEOMA Business School": "제한 없음",
    "University of Vaasa": "제한 없음",
    "Renmin Business School, Renmin University of China": "제한 없음",
    "Simon Fraser University": "제한 없음",
}

NO_REQ = re.compile(r"(?i)^(none|no requirements?|not applicable)$")
NA = re.compile(r"(?i)^(n/?a\.?|-)$")


def normalize(v):
    v = re.sub(r"\s+", " ", str(v)).strip()
    if not v:
        return "제한 없음"  # 시트 원문 'None' → 추출 단계에서 빈 값이 된 케이스
    if v in KEEP or v.endswith("이상") or "상이" in v or v in ("제한 없음", "명시 없음", "홈교 기준"):
        return v
    if v.startswith(("제한 없음", "명시 없음", "홈교 기준")):
        return v
    if NO_REQ.match(v):
        return "제한 없음"
    if NA.match(v):
        return "명시 없음"
    m = re.match(r"^(?:최소 )?(\d)학기$", v)
    if m:
        return f"{m.group(1)}학기 이상"
    return None


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    n, left = 0, []
    for rec in data:
        g = rec.get("semesters")
        if not isinstance(g, dict):
            g = {"value": g, "source": "시트"}
            rec["semesters"] = g
        v = str(g.get("value") or "").strip()
        if rec["university"] in MANUAL:
            new = MANUAL[rec["university"]]
        else:
            new = normalize(v)
        if new is None:
            left.append((rec["university"], v))
        elif new != v:
            g["value"] = new
            n += 1

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"변환 {n}건, 미처리 {len(left)}건")
    for u, v in left:
        print(f"  {u}: {v[:100]!r}")


if __name__ == "__main__":
    main()

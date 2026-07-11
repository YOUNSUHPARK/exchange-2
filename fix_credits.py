"""최소/최대 학점 일관 표기 정리 (2026-07-12, 사용자 지침 반영).

표기 규칙:
- "N ECTS" / "N~M ECTS" (유럽), "N US credits"(미국), 그 외 "N credits" 등 숫자+단위
- 제한 없음 → '제한 없음', 수치 미기재 → '명시 없음', 홈교 재량 → '홈교 기준'
- '담당자 이메일 문의'/'확인필요' 유지, 빈 값 → '확인필요'
- 비자 요건형(일본 3곳)은 사용자 지시로 '명시 없음'
실행 후: python build_table.py && python build_site.py
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

KEEP = ("담당자 이메일 문의", "확인필요")

ECTS_COUNTRIES = {
    "AUSTRIA", "BELGIUM", "CROATIA", "CZECH REPUBLIC", "DENMARK", "ESTONIA",
    "FINLAND", "FRANCE", "GERMANY", "HUNGARY", "ITALY", "LITHUANIA",
    "NETHERLANDS", "NORWAY", "POLAND", "PORTUGAL", "SPAIN", "SWEDEN",
    "SWITZERLAND", "TURKEY",
}

# (대학명, 필드) → 확정 값. src를 함께 지정하면 출처 라벨 교체(웹 검증분).
MANUAL = {
    # 웹 확인 (2026-07-12)
    ("University of Technology Sydney", "min"): ("18 credit points", "웹"),
    ("University of Technology Sydney", "max"): ("24 credit points", "웹"),
    ("University of Montreal", "min"): ("12 credits (학부)", "웹"),
    ("University of Montreal", "max"): ("15 credits (학부)", "웹"),
    ("Charles University", "min"): ("4과목 (학부; 대학원 3과목)", "웹"),
    ("Polytechnic University of Milan", "min"): ("확인필요", None),
    ("Polytechnic University of Milan", "max"): ("확인필요", None),
    ("Toyo University", "min"): ("명시 없음", "웹"),
    ("Toyo University", "max"): ("제한 없음", "웹"),
    ("Toulouse Business School", "min"): ("24 ECTS", "웹"),
    ("Toulouse Business School", "max"): ("명시 없음", "웹"),
    ("Nanyang Technological University (NTU)", "min"): ("제한 없음", "웹"),
    ("Nanyang Technological University (NTU)", "max"): ("20 AU (6과목)", "웹"),
    ("Kyushu University", "min"): ("6과목 (JTW, 과목당 보통 2 credits)", "웹"),
    # 사용자 결정 (2026-07-12)
    ("University of Indonesia", "min"): ("명시 없음", None),
    ("University of Indonesia", "max"): ("15 credits", None),
    ("Hitotsubashi University", "min"): ("명시 없음", None),
    ("Ritsumeikan University", "min"): ("명시 없음", None),
    ("Hokkaido University", "min"): ("명시 없음", None),
    ("Hokkaido University", "max"): ("명시 없음", None),
}

# 2차: 1차 규칙 변환 후 남은 학교별 고유 표기 정리 (값 근거는 시트 원문)
MANUAL2 = {
    ("The University of Melbourne", "min"): "37.5 credit points",
    ("The University of Melbourne", "max"): "50 credit points",
    ("University of Newcastle", "min"): "30~40 units (3~4과목)",
    ("University of Newcastle", "max"): "50 units (5과목)",
    ("Swinburne University of Technology", "min"): "37.5 credit points",
    ("Swinburne University of Technology", "max"): "50 credit points",
    ("University of Western Australia(UWA)", "min"): "18 UWA credit points (22.5 ECTS)",
    ("University of Western Australia(UWA)", "max"): "24 UWA credit points (30 ECTS)",
    ("The University of New South Wales", "min"): "18 UoC",
    ("The University of New South Wales", "max"): "24 UoC",
    ("Queensland University of Technology", "min"): "36 QUT credits (22.5 ECTS)",
    ("Queensland University of Technology", "max"): "48 QUT credits (30 ECTS)",
    ("University of the Sunshine Coast", "min"): "3과목",
    ("University of the Sunshine Coast", "max"): "4과목",
    ("FHS, Kufstein Tirol University of Applied Sciences", "min"): "21 ECTS (증감 시 홈교 확인)",
    ("Free University of Brussels (ULB)", "min"): "5 ECTS (1과목)",
    ("University of Liege", "min"): "10 ECTS (+프랑스어 야간강좌)",
    ("Unisinos University", "min"): "16 Unisinos credits",
    ("Okanagan College", "min"): "9 credits (3과목)",
    ("Okanagan College", "max"): "15 credits (5과목)",
    ("York University", "min"): "9 York credits",
    ("York University", "max"): "15 York credits",
    ("University of Saskatchewan", "min"): "9 credit units (3과목)",
    ("University of Saskatchewan", "max"): "15 credit units (5과목)",
    ("Simon Fraser University", "min"): "9 SFU units (3과목)",
    ("Simon Fraser University", "max"): "18 SFU units (4~5과목, 비권장)",
    ("HEC Montreal", "min"): "12 credits (4과목)",
    ("HEC Montreal", "max"): "15 credits (5과목)",
    ("Communication University of China", "max"): "12 credits",
    ("Huazhong University of Science and Technology", "min"): "전공별 상이",
    ("Huazhong University of Science and Technology", "max"): "전공별 상이",
    ("Renmin Business School, Renmin University of China", "min"): "제한 없음",
    ("Renmin Business School, Renmin University of China", "max"): "제한 없음",
    ("BEIJING NORMAL UNIVERSITY", "max"): "26 credits",
    ("University of Zagreb", "min"): "20 ECTS (권장)",
    ("University of Zagreb", "max"): "30 ECTS (권장)",
    ("Masaryk University", "min"): "20 ECTS",
    ("Masaryk University", "max"): "제한 없음 (현실적 최대 35~40 ECTS)",
    ("Aalborg University", "max"): "30 ECTS",
    ("University of Vaasa", "min"): "명시 없음 (통상 20~30 ECTS)",
    ("University of Vaasa", "max"): "제한 없음 (권장 20~30 ECTS)",
    ("Hanken School of Economics", "min"): "24~30 ECTS",
    ("Aalto University", "min"): "명시 없음 (통상 30 ECTS)",
    ("Aalto University", "max"): "제한 없음 (통상 30 ECTS)",
    ("Sup Biotech", "min"): "확인필요",  # 원문 '180 ECTS'는 학기 부하가 아니라 이수요건으로 보임
    ("Jean Moulin University Lyon 3", "min"): "8 ECTS",
    ("Jean Moulin University Lyon 3", "max"): "제한 없음 (SELF 프로그램은 31 ECTS)",
    ("SKEMA Business School", "max"): "30 ECTS (프로그램에 따라 21 ECTS)",
    ("Paris 1 Pantheon-Sorbonne University", "min"): "학과별 상이",
    ("Paris 1 Pantheon-Sorbonne University", "max"): "학과별 상이",
    ("Leuphana University Luneburg", "min"): "명시 없음 (통상 30 ECTS)",
    ("Leuphana University Luneburg", "max"): "명시 없음 (모듈당 5 ECTS)",
    ("University of Cologne", "max"): "명시 없음 (통상 30 ECTS/5과목)",
    ("Kiel University", "max"): "약 25~30 ECTS",
    ("Frankfurt School of Finance and Management", "min"): "6 ECTS (1모듈)",
    ("Frankfurt School of Finance and Management", "max"): "30 ECTS (5모듈)",
    ("University of Bonn", "min"): "명시 없음 (권장 약 30 ECTS)",
    ("University of Bonn", "max"): "명시 없음 (권장 약 30 ECTS)",
    ("Friedrich–Alexander University", "max"): "30 ECTS (권장)",
    ("The Chinese University of Hong Kong", "min"): "9 units",
    ("The Chinese University of Hong Kong", "max"): "18 units",
    ("University of Verona", "min"): "명시 없음",
    ("University of Verona", "max"): "제한 없음",
    ("Ca' Foscari University of Venice", "max"): "30 ECTS",
    ("Bocconi University", "min"): "명시 없음 (최소 1과목)",
    ("Bocconi University", "max"): "제한 없음 (최대 5과목)",
    ("Okayama University", "min"): "10 credits",
    ("Hitotsubashi University", "max"): "14 credits/쿼터 (28 credits/학기)",
    ("Ritsumeikan University", "max"): "20 credits",
    ("Chuo University", "min"): "명시 없음",
    ("Shinshu University", "min"): "7 credits",
    ("Nagoya University", "min"): "15 credits (연간 30)",
    ("Tohoku University", "min"): "프로그램별 상이 (COLABS/JYPE/DEEP/IPLA)",
    ("Tohoku University", "max"): "24 credits",
    ("KIMEP University", "min"): "9 US credits (15 ECTS)",
    ("KIMEP University", "max"): "18 US credits (30 ECTS)",
    ("Vytautas Magnus University", "max"): "36 ECTS (권장)",
    ("Tecnologico de Monterrey (ITESM)", "min"): "3 TEC credits (약 5 ECTS)",
    ("Tecnologico de Monterrey (ITESM)", "max"): "18 TEC credits (약 30 ECTS)",
    ("Radboud University", "min"): "제한 없음 (비자상 25 ECTS 필요)",
    ("Radboud University", "max"): "제한 없음 (통상 30 ECTS)",
    ("Tilburg University", "min"): "1과목 (보통 6 ECTS)",
    ("Maastricht University", "min"): "학부별 상이 (UCM 20 ECTS 등)",
    ("Maastricht University", "max"): "30 ECTS (학부별 상이)",
    ("Inholland University of Applied Sciences", "min"): "30 ECTS (고정 패키지)",
    ("Inholland University of Applied Sciences", "max"): "30 ECTS (고정 패키지)",
    ("Erasmus University Rotterdam", "min"): "24 ECTS (권장)",
    ("HU University of Applied Sciences Utrecht", "max"): "35 ECTS",
    ("Vrije Universiteit Amsterdam", "min"): "24 ECTS",
    ("Vrije Universiteit Amsterdam", "max"): "36 ECTS",
    ("University of Oslo", "min"): "명시 없음 (풀타임 기대)",
    ("Pontifical Catholic University of Peru", "min"): "1과목 이상",
    ("Pontifical Catholic University of Peru", "max"): "22 PUCP credits (권장 12~15)",
    ("Instituto Superior Tecnico (IST)", "min"): "6 ECTS",
    ("Singapore University of Technology and Design (SUTD)", "min"): "24 SUTD credits",
    ("Singapore University of Technology and Design (SUTD)", "max"): "48 SUTD credits",
    ("Singapore Management University", "min"): "2 SMU credits",
    ("Singapore Management University", "max"): "4 SMU credits",
    ("Autonomous University of Barcelona", "min"): "명시 없음 (비자 요건 유의)",
    ("IE University", "max"): "30 ECTS (+선택 스페인어 3 ECTS)",
    ("Uppsala University", "min"): "22.5 credits (비EU 비자는 30 필요)",
    ("Uppsala University", "max"): "37.5 credits",
    ("University of Applied Sciences and Arts Northwestern Switzerland", "min"): "15 ECTS",
    ("University of Applied Sciences and Arts Northwestern Switzerland", "max"): "30~33 ECTS (권장)",
    ("University of Bern", "min"): "명시 없음 (권장 20~25 ECTS)",
    ("Feng Chia University", "min"): "12 credits (학부) / 3 (대학원)",
    ("Feng Chia University", "max"): "25 credits (학부) / 12 (대학원)",
    ("National Tsing Hua University", "min"): "9 credits (학부; 대학원 1과목)",
    ("National Tsing Hua University", "max"): "25 credits (학부)",
    ("National Chiao Tung University", "min"): "9 NYCU credits (18 ECTS)",
    ("National Taiwan University", "min"): "4 credits (2과목)",
    ("National Taiwan University", "max"): "25 credits (학부) / 20 (대학원)",
    ("Chulalongkorn University", "max"): "22 credits (학부) / 6 (대학원)",
    ("Ankara University", "max"): "단과대별 상이",
    ("Bogazici University", "min"): "17~21 Bogazici credits (약 20~30 ECTS, 4~6과목)",
    ("SOAS University of London", "min"): "45 UK credits",
    ("SOAS University of London", "max"): "60 UK credits",
    ("University of Sheffield", "min"): "40 UK credits",
    ("University of Sheffield", "max"): "60 UK credits (30 ECTS)",
    ("University of Reading", "min"): "20 ECTS",
    ("University of Reading", "max"): "30 ECTS",
    ("University of Exeter", "max"): "45 Exeter credits (22.5 ECTS)",
    ("University of Essex", "min"): "60 Essex credits (30 ECTS)",
    ("University of Essex", "max"): "60 Essex credits (30 ECTS)",
    ("University of Bristol", "min"): "60 Bristol credits (30 ECTS)",
    ("University of Bristol", "max"): "60 Bristol credits (30 ECTS)",
    ("University of the West of England(UWE Bristol)", "min"): "명시 없음 (권장 15 ECTS 이상)",
    ("Durham University", "min"): "120 Durham credits (연간)",
    ("Durham University", "max"): "120 Durham credits (연간)",
    ("University of Central Lancashire", "min"): "60 UK credits (연간 120)",
    ("University of Central Lancashire", "max"): "60 UK credits (연간 120)",
    ("Birmingham City University", "min"): "60 BCU credits (30 ECTS)",
    ("Birmingham City University", "max"): "60 BCU credits (30 ECTS)",
    ("Clarkson University", "min"): "12 US credits (약 4과목)",
    ("Clarkson University", "max"): "18 US credits (약 6과목)",
    ("University of Texas at Dallas", "min"): "12 US credits",
    ("University of Texas at Dallas", "max"): "18 US credits (권장 15)",
    ("University of Massachusetts Boston", "min"): "12 US credits (학부) / 9 (대학원)",
    ("University of Massachusetts Boston", "max"): "17 US credits (학부) / 12 (대학원)",
    ("University of Illinois Springfield", "min"): "12 US credits",
    ("University of Houston", "min"): "12 US credits (24 ECTS)",
    ("University of Houston", "max"): "18 US credits (36 ECTS)",
    ("Arizona State University", "min"): "12 US credits (학부) / 9 (대학원)",
    ("State University of New York at Buffalo", "max"): "19 US credits (학부) / 16 (대학원)",
    ("The Pennsylvania State University", "max"): "19 US credits (연간 30)",
    ("University of Wisconsin-Milwaukee", "min"): "12 US credits",
    ("University of Wisconsin-Milwaukee", "max"): "18 US credits",
    ("University of California, Santa Cruz", "min"): "12 US credits/쿼터",
    ("University of California, Santa Cruz", "max"): "19 US credits/쿼터",
    ("College of Charleston", "min"): "12 US credits (24 ECTS)",
    ("College of Charleston", "max"): "15 US credits (30 ECTS)",
    ("University of North Carolina at Chapel Hill", "min"): "12 US credits (학부)",
    ("Florida State University", "min"): "12 US credits",
    ("Florida State University", "max"): "15 US credits (12 초과 시 SKKU 승인 필요)",
}
MANUAL.update({k: (v, None) for k, v in MANUAL2.items()})

# 이미 정리된 최종 형태 (재실행 시 그대로 통과)
ACCEPT = re.compile(
    r"^(제한 없음|명시 없음|홈교 기준|확인필요|담당자 이메일 문의|전공별 상이|학과별 상이|"
    r"학부별 상이|프로그램별 상이|단과대별 상이)( \(.*\))?$"
    r"|^\d+(\.\d+)?(~\d+(\.\d+)?)? (ECTS|US credits|UK credits|credits|credit points|units|UoC|AU)( \(.*\))?$"
)

NO_LIMIT = re.compile(
    r"(?i)^(no limits?|none|no|n/?a\.?|not specified|no requirements?|no restriction|"
    r"no max(imum)?( has been set\.?)?|there is no (maximum|upper) .*|there is not maximum.*|"
    r"no maximum, subject to availability|\(there is no particular limit\)|-)$"
)
HOME_UNIV = re.compile(
    r"(?i)(home (universi|institu|school)|up to skku|skku decides|up to partner|"
    r"home university of the student|depends on skku)"
)


def _num(s):
    f = float(s)
    return str(int(f)) if f == int(f) else str(f)


def normalize(v, country, field):
    """규칙 변환. 확정 못 하면 None."""
    v = re.sub(r"\s+", " ", str(v)).strip()
    if not v:
        return "확인필요"
    if v in KEEP or ACCEPT.match(v):
        return v
    if NO_LIMIT.match(v):
        return "제한 없음" if field == "max" else "명시 없음"
    if HOME_UNIV.search(v):
        return "홈교 기준"

    # "24-30 ECTS", "30 ECTS per semester", "30ECTS", "20 ECT/semester", "30 ects"
    m = re.match(r"(?i)^(?:minimum|maximum|max\.?|min\.?|recommended)?[:\s]*"
                 r"(\d+(?:[.,]\d+)?)\s*(?:-|~|to)?\s*(\d+(?:[.,]\d+)?)?\s*"
                 r"ects?s?\b(?:\s*credits?)?(?:\s*(?:per|/)\s*semester)?"
                 r"(?:\s*\((?:recommended)\))?\s*\.?$", v)
    if m:
        a = _num(m.group(1).replace(",", "."))
        return f"{a}~{_num(m.group(2))} ECTS" if m.group(2) else f"{a} ECTS"

    # 순수 숫자 → 국가별 단위
    m = re.match(r"^(\d+(?:\.\d+)?)$", v)
    if m:
        n = _num(m.group(1))
        if country in ECTS_COUNTRIES:
            return f"{n} ECTS"
        if country == "UNITED STATES":
            return f"{n} US credits"
        if country == "UNITED KINGDOM":
            return f"{n} UK credits"
        return f"{n} credits"

    # "12 credits", "12 US credits", "minimum 12 credits", "at least 12 credits",
    # "no more than 22 credits", "12 credits per semester", "Maximum 21 credits"
    m = re.match(r"(?i)^(?:minimum|maximum|at least|no more than)?\s*"
                 r"(\d+(?:\.\d+)?)\s*(u\.?s\.?\s*)?credits?(?:\s*hours?)?"
                 r"(?:\s*(?:per|/)\s*(?:semester|quarter))?\s*\.?$", v)
    if m:
        n = _num(m.group(1))
        unit = "US credits" if (m.group(2) or country == "UNITED STATES") else "credits"
        return f"{n} {unit}"

    return None


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    n, left = 0, []
    for rec in data:
        for field in ("min", "max"):
            key = f"credits_{field}"
            g = rec[key]
            if not isinstance(g, dict):
                g = {"value": g, "source": "시트"}
                rec[key] = g
            v = str(g.get("value") or "").strip()
            mk = (rec["university"], field)
            if mk in MANUAL:
                new, src = MANUAL[mk]
                if src:
                    g["source"] = src
            else:
                new = normalize(v, rec["country"], field)
            if new is None:
                left.append((rec["university"], rec["country"], field, v))
            elif new != v:
                g["value"] = new
                n += 1

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"변환 {n}건, 미처리 {len(left)}건")
    for u, c, f_, v in left:
        print(f"  [{f_}] {u} ({c}): {v[:120]!r}")


if __name__ == "__main__":
    main()

"""최소 GPA를 N/N 형식으로 통일 (2026-07-12).

- 기계적 패턴("3.0 out of 4.0", "3.0 on a 4.0 scale", "GPA 2.5/4.0" 등) → norm_gpa()
- 특수 케이스(등급제·복수 기준·스케일만 기재 등) → MANUAL
- '담당자 이메일 문의'/'확인필요'/'제한 없음/명시 없음'은 그대로 둠
실행 후: python build_table.py && python build_site.py
"""
import io
import json
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SKIP = ("담당자 이메일 문의", "확인필요", "제한 없음/명시 없음")

# 값에 근거해 개별 확정한 표기 (원문은 git 이력·data.json 이전 버전 참조)
MANUAL = {
    "The Australian National University": "4.0/7.0",
    "Queensland University of Technology": "2.5/4.0",
    "Haaga-Helia University of Applied Sciences": "3.0/5.0",           # 3 on a scale 1-5
    "Okanagan College": "60/100",
    "Toronto Metropolitan University": "2.5/4.0",                      # or 70% 동일 기준
    "Universidad San Francisco de Quito": "2.5/4.0 (갈라파고스 캠퍼스 3.0/4.0)",
    "The University of Hong Kong": "3.3/4.3 (법·경영 제외 전공은 3.0/4.0)",
    "University of Pecs": "2.5/4.0 (또는 3.5/5.0)",
    "Tohoku University": "2.3/3.0 (장학금 기준, 지원 필수 아님)",
    "Vytautas Magnus University": "70/100",
    "Tecnologico de Monterrey (ITESM)": "2.5/4.0 (멕시코식 80/100)",
    "Maastricht University": "3.0/4.0 (경영경제대학 SBE는 제한 없음)",
    "Erasmus University Rotterdam": "명시 없음 (미시·거시경제, 통계, 수학 선수과목 요구)",
    "University of Oslo": "C 이상 (ECTS 등급)",
    "Nanyang Technological University (NTU)": "3.3/5.0",
    "SOAS University of London": "3.3/4.0 (학업동기 우수 시 3.0/4.0)",
    "University of Sheffield": "50/100 (UK 2:2)",
    "University of Bristol": "3.0/4.0 (또는 3.5/5.0, 80/100)",
    "National Chiao Tung University": "2.75~3.0/4.0 (전공별 상이)",
    "University of Texas at Dallas": "3.0/4.0",                        # 미국 4.0 스케일 가정
    "Hacettepe University": "명시 없음 (4.0 스케일만 기재)",
    "INSEEC Business School": "명시 없음 (프랑스식 0~20 체계)",
    "EDHEC Business School": "명시 없음 (우수한 성적 요구)",
    "Vorarlberg University of Applied Sciences": "제한 없음 (홈교 기준)",
    "University of Manitoba": "Good standing (수치 기준 없음)",
    "The Chinese University of Hong Kong": "Good standing (수치 기준 없음)",
    "Fontys University of Applied Sciences": "프로그램별 상이",
    "Bocconi University": "제한 없음/명시 없음",                        # GPA 요건 없음 명시(18~30 스케일 설명뿐)
    "ICN Business School": "제한 없음 (학년별 최소 이수학점/ECTS 요건만)",
}

_PAT = re.compile(
    r"(?i)^\s*(?:gpa\s*)?(\d+(?:\.\d+)?)\s*"
    r"(?:/|out of|on a|on)\s*(?:a\s*)?(\d+(?:\.\d+)?)"
    r"(?:[-\s]*point)?(?:\s*scale)?(?:\s*\(undergraduates?\))?(?:\s*cumulative\s*GPA)?\s*$"
)


def _fmt(x):
    f = float(x)
    if f >= 10:  # 20·100점 만점 등은 정수 표기
        return str(int(f)) if f == int(f) else str(f)
    s = f"{f:.2f}".rstrip("0").rstrip(".")
    return s if "." in s else f"{s}.0"


def norm_gpa(v):
    """기계적 패턴이면 'N/N'으로, 아니면 None."""
    if not v:
        return None
    m = _PAT.match(str(v).strip())
    if not m:
        return None
    a, b = float(m.group(1)), float(m.group(2))
    if not (0 < a <= b <= 100):  # 상식 범위 밖이면 건드리지 않음
        return None
    return f"{_fmt(a)}/{_fmt(b)}"


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    pat_ok = re.compile(r"^\d+(\.\d+)?/\d+(\.\d+)?( \(.*\))?$")
    n = 0
    left = []
    for rec in data:
        g = rec["gpa_min"]
        v = str(g.get("value") or "").strip()
        if rec["university"] in MANUAL:
            new = MANUAL[rec["university"]]
        elif not v or v in SKIP or pat_ok.match(v):
            continue  # 값 없음 / 이메일문의·확인필요·제한없음 / 이미 N/N
        else:
            new = norm_gpa(v)
        if new and new != v:
            print(f"  {rec['university']}: {v!r} → {new!r}")
            g["value"] = new
            n += 1
        elif not new and not pat_ok.match(v):
            left.append((rec["university"], v))

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"\n변환 {n}건")
    if left:
        print("=== 미변환 잔여 (수동 확인 필요) ===")
        for u, v in left:
            print(f"  {u}: {v!r}")


if __name__ == "__main__":
    main()

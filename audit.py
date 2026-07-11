"""data.json 이상값 스캔 → review_checklist.csv. 수작업 검수 진행률 확인용.

실행: python audit.py  (PLAN_정확도개선.md 참조)
"""
import json, re, csv, os
from collections import Counter
import config

def v(o):
    return (o.get("value") if isinstance(o, dict) else o) or ""

def scan(data):
    issues = []
    for r in data:
        uni, c = r["university"], r["country"]
        def add(field, val, why):
            issues.append([c, uni, field, str(val)[:90], why])
        lr = v(r["lang_req"])
        if lr in ("확인필요", "확인필요(링크 참조)"):
            add("어학요건", lr, "미확보")
        elif "http" in lr:
            add("어학요건", lr, "URL만 있음")
        elif len(lr) > 90:
            add("어학요건", lr, "너무 김(압축 필요)")
        elif re.search(r"iBT\s*[0-4][^0-9]|IELTS\s*[0-3][^.0-9]", lr):
            add("어학요건", lr, "subscore 의심(점수 비정상)")
        elif not re.search(r"\d", lr) and "문의" not in lr:
            add("어학요건", lr, "점수 없음(문장만)")
        g = v(r["gpa_min"])
        if g == "확인필요":
            add("최소GPA", g, "미확보")
        elif "http" in g:
            add("최소GPA", g, "URL만 있음")
        elif len(g) > 40 and "문의" not in g:
            add("최소GPA", g, "문장형(정규화 필요)")
        if v(r["lang_instruction"]) == "확인필요":
            add("수업언어", "확인필요", "미확보")
        if "|" in v(r["lang_instruction"]):
            add("수업언어", v(r["lang_instruction"]), "복수값(단일화 필요)")
        for k, label in [("credits_min", "최소학점"), ("credits_max", "최대학점")]:
            val = r.get(k) or ""
            if len(str(val)) > 50:
                add(label, val, "너무 김")
        if not r.get("semesters"):
            add("학기수", "(비어있음)", "미확보")
        ma = v(r["major_abroad"])
        if len(ma) > 100:
            add("해외수학전공", ma, "너무 김(요약 필요)")
    return issues

def main():
    path = os.path.join(config.HERE, "data.json")
    data = json.load(open(path, encoding="utf-8"))
    issues = scan(data)
    out = os.path.join(config.HERE, "review_checklist.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["국가", "대학명", "항목", "현재값", "문제"])
        w.writerows(issues)
    print(f"총 이상 항목: {len(issues)} | 대학 수: {len({i[1] for i in issues})} → {out}")
    for k, n in Counter(i[4] for i in issues).most_common():
        print(f"  {k}: {n}")

if __name__ == "__main__":
    main()

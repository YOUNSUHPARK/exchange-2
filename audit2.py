"""전수 품질 감사 (2026-07-12): 형식 준수 + 필드 간 교차 일관성.

실행: python audit2.py → 콘솔 요약 + audit_report.csv
"""
import csv
import io
import json
import re
import sys

import location as loc_mod

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OK_COMMON = ("담당자 이메일 문의", "확인필요")


def v(o):
    return (o.get("value") if isinstance(o, dict) else o) or ""


def src(o):
    return (o.get("source") if isinstance(o, dict) else "") or ""


GPA_OK = re.compile(
    r"^(\d+(\.\d+)?(~\d+(\.\d+)?)?/\d+(\.\d+)?( \(.*\))?|제한 없음.*|명시 없음.*|"
    r"Good standing.*|프로그램별 상이|C 이상.*|홈교 기준)$")
SEM_OK = re.compile(
    r"^(\d(~\d)?학기 이상.*|제한 없음.*|명시 없음.*|.*상이.*|홈교 기준)$")
CRD_OK = re.compile(
    r"^(약 )?\d+(\.\d+)?(~\d+(\.\d+)?)? ?[A-Za-z가-힣].{0,40}$|"
    r"^(제한 없음|명시 없음)( \(.*\))?$|^홈교 기준$|^.*상이.*$|^\d과목.*$|^1과목.*$")
LANGS = ("영어", "독일어", "프랑스어", "일본어", "중국어", "스페인어", "이탈리아어",
         "포르투갈어", "네덜란드어", "폴란드어", "헝가리어", "인도네시아어", "터키어",
         "태국어", "체코어", "크로아티아어", "덴마크어", "에스토니아어", "핀란드어",
         "리투아니아어", "노르웨이어", "스웨덴어", "러시아어", "베트남어")
REQ_OK_HINT = ("점 이상", "이상", "공인성적 불요", "SKKU", "명시 없음", "상이", "요구", "증명", "CEFR")
TIERS = ("도시", "준도시", "도시 외곽")
# CET는 제외: 미국 대학도 중국어권 지원자용으로 인정하는 사례 확인됨(Wyoming, 2026-07-12 검증)
LOCAL_TESTS = {"JLPT": "일본어", "HSK": "중국어", "TOCFL": "중국어", "DELF": "프랑스어",
               "DALF": "프랑스어", "TCF": "프랑스어"}


def parse_credit_num(s):
    m = re.match(r"^(약 )?(\d+(\.\d+)?)", s)
    return float(m.group(2)) if m else None


def unit_of(s):
    m = re.match(r"^(약 )?\d+(\.\d+)?(~\d+(\.\d+)?)?\s*([A-Za-z가-힣 ]+?)(\s*\(|/|$)", s)
    return (m.group(5) or "").strip() if m else ""


def scan(data):
    issues = []  # (severity, country, uni, field, value, why)
    for r in data:
        uni, c = r["university"], r["country"]

        def add(sev, field, val, why):
            issues.append([sev, c, uni, field, str(val)[:80], why])

        # ── 형식 검사 ─────────────────────────────
        g = v(r["gpa_min"])
        if g not in OK_COMMON and not GPA_OK.match(g):
            add("형식", "최소GPA", g, "표준 형식 아님")
        s = v(r["semesters"])
        if s not in OK_COMMON and not SEM_OK.match(s):
            add("형식", "완료학기", s, "표준 형식 아님")
        for k, lab in (("credits_min", "최소학점"), ("credits_max", "최대학점")):
            cv = v(r[k])
            if cv not in OK_COMMON and not CRD_OK.match(cv):
                add("형식", lab, cv, "표준 형식 아님")
        li = v(r["lang_instruction"])
        li_parts = [p.strip() for p in li.split(",")]
        if li not in OK_COMMON and not all(
                any(p.startswith(l) for l in LANGS) for p in li_parts):
            add("형식", "수업언어", li, "언어명 형식 아님")
        lr = v(r["lang_req"])
        if lr not in OK_COMMON and not any(h in lr for h in REQ_OK_HINT):
            add("형식", "어학요건", lr, "표준 형식 아님")
        lo = r["location"]
        if v(lo) != "확인필요":
            if lo.get("tier") not in TIERS:
                add("형식", "위치", v(lo), "tier 비정상")
            if " — " not in v(lo):
                add("형식", "위치", v(lo), "라벨—설명 형식 아님")

        # ── 교차 일관성 ───────────────────────────
        # 위치: 저장된 사실값으로 tier 재계산 일치 확인
        if lo.get("city_size"):
            want = loc_mod.classify_tier(lo["city_size"], lo.get("commute_min") or 0,
                                         lo.get("major_city_min"))
            if want != lo.get("tier"):
                add("모순", "위치", f"{lo.get('tier')} (재계산={want})", "tier 재계산 불일치")
        # 학점: min > max (같은 단위일 때만)
        cmin, cmax = v(r["credits_min"]), v(r["credits_max"])
        nmin, nmax = parse_credit_num(cmin), parse_credit_num(cmax)
        if nmin and nmax and unit_of(cmin) == unit_of(cmax) and nmin > nmax:
            add("모순", "학점", f"min {cmin} > max {cmax}", "최소>최대")
        # 수업언어 vs 어학요건: 영어 단독 수업인데 현지어 시험만 요구 등
        if li and li not in OK_COMMON:
            langs_in = set(p.split()[0] if " " in p else p for p in li_parts)
            for test, lang in LOCAL_TESTS.items():
                if test in lr and lang not in li and "영어" in li and len(li_parts) == 1:
                    add("모순", "언어정합", f"수업={li}, 요건에 {test}", "영어 수업인데 현지어 시험")
        # 출처 라벨 누락
        for k, lab in (("gpa_min", "최소GPA"), ("lang_req", "어학요건"),
                       ("lang_instruction", "수업언어"), ("location", "위치"),
                       ("semesters", "완료학기"), ("credits_min", "최소학점"),
                       ("credits_max", "최대학점")):
            if v(r[k]) and not src(r[k]):
                add("출처", lab, v(r[k]), "출처 라벨 없음")
        # 특징 검사
        feats = r.get("features") or []
        texts = [f["text"] for f in feats]
        if len(texts) != len(set(texts)):
            add("형식", "특징", " / ".join(texts), "중복 특징")
        for f in feats:
            if f.get("source") not in ("자동", "웹", "시트", "AI추정"):
                add("출처", "특징", f.get("text"), "출처 라벨 비정상")
            if len(f.get("text", "")) > 45:
                add("형식", "특징", f.get("text"), "45자 초과")

        # ── 커버리지(오류 아님, 집계용) ────────────
        for k, lab in (("gpa_min", "최소GPA"), ("lang_req", "어학요건"),
                       ("lang_instruction", "수업언어"),
                       ("credits_min", "최소학점"), ("credits_max", "최대학점"),
                       ("semesters", "완료학기")):
            if v(r[k]) in OK_COMMON:
                add("커버리지", lab, v(r[k]), "미확보(문의/확인필요)")
    return issues


def main():
    data = json.load(open("data.json", encoding="utf-8"))
    issues = scan(data)
    with open("audit_report.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["구분", "국가", "대학", "항목", "값", "문제"])
        w.writerows(issues)

    from collections import Counter
    by_sev = Counter(i[0] for i in issues)
    n_fields = len(data) * 8  # 8개 표시 필드 기준
    hard = sum(n for k, n in by_sev.items() if k in ("형식", "모순", "출처"))
    print(f"검사 대상: {len(data)}개교 × 8필드 = {n_fields}")
    print(f"구분별: {dict(by_sev)}")
    print(f"형식·모순·출처 문제(실오류 후보): {hard}건 → 형식적 정합률 {(1 - hard / n_fields) * 100:.2f}%")
    print("\n=== 실오류 후보 상세 ===")
    for i in issues:
        if i[0] != "커버리지":
            print(f"  [{i[0]}] {i[2]} ({i[1]}) {i[3]}: {i[4]!r} — {i[5]}")


if __name__ == "__main__":
    main()

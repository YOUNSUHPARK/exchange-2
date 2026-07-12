"""오케스트레이터: 로드 → 크롤 → Solar 추출/위치 → 병합 → data.json → 표+웹사이트.

사용법:
  python run.py --country "UNITED STATES"        # US 전체
  python run.py --country "UNITED STATES" --limit 3
  python run.py --no-crawl                        # 크롤 생략(캐시만)
"""
import argparse
import json
import os
import re
import sys

import config
import loader
import fetcher
import extract
import location
import lang_map


def norm_semesters(v):
    if v is None:
        return None
    s = str(v).strip()
    if re.match(r"(?i)^(none|no requirements?|not applicable)$", s):
        return "제한 없음"
    if re.match(r"(?i)^(n/?a\.?|-)$", s):
        return "명시 없음"
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    def fmt(x):
        x = float(x)
        return str(int(x)) if x == int(x) else str(x)
    # 학기 수로 볼 수 없는 숫자(60 ECTS, 연도 등)가 섞이면 원문 보존 → 수동 검수 대상
    if not nums or any(float(x) > 12 for x in nums):
        return s
    prefix = "최소 " if re.search(r"at least|minimum|이상|최소", s, re.I) else ""
    if len(nums) >= 2 and nums[0] != nums[1]:
        return f"{prefix}{fmt(nums[0])}~{fmt(nums[1])}학기"
    return f"{prefix}{fmt(nums[0])}학기"


def looks_like_gpa(s):
    if not s:
        return False
    s = str(s)
    if re.search(r"\d\s*/\s*\d", s):          # 3.0/4.0
        return True
    if re.search(r"\bGPA\b", s, re.I) and re.search(r"\d", s):
        return True
    if re.search(r"\d\.\d.*(scale|만점)", s, re.I):
        return True
    return False


def is_url_only(s):
    if not s:
        return False
    s = str(s).strip()
    return s.startswith("http") and " " not in s


def pick(field_obj):
    """Solar 추출 결과 {value, source, evidence} 안전 파싱."""
    if not isinstance(field_obj, dict):
        return None, config.SRC_UNKNOWN, ""
    v = field_obj.get("value")
    if v in (None, "", "null", "N/A", "n/a"):
        return None, "none", field_obj.get("evidence", "")
    src = field_obj.get("source", "none")
    label = {"web": config.SRC_WEB, "factsheet": config.SRC_FACTSHEET,
             "sheet": config.SRC_SHEET, "none": config.SRC_UNKNOWN}.get(src, config.SRC_WEB)
    return str(v).strip(), label, field_obj.get("evidence", "")


UNAVAILABLE_RE = re.compile(r"on\s*fact\s*sheet|please\s*(see|refer|visit)|tba|미정", re.I)


def clean_or_email(value, email):
    """시트값이 'On fact sheet' 류로 사실상 비어있으면 이메일 문의로 대체."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if UNAVAILABLE_RE.search(s) and email:
        return config.EMAIL_INQUIRY_TEXT
    if UNAVAILABLE_RE.search(s):
        return "확인필요"
    return s


def build_record(rec, ex, loc):
    sheet = rec["sheet"]
    email = sheet.get("email")

    # 캠퍼스: Solar 정리값 우선, 없으면 시트 D(URL만이면 확인필요)
    cval, csrc, _ = pick(ex.get("campus", {}))
    if not cval:
        d = sheet.get("campus")
        if d and not is_url_only(d):
            cval, csrc = d, config.SRC_SHEET
        elif d:
            cval, csrc = "홈페이지 참조(링크)", config.SRC_UNKNOWN
    campus = {"value": cval, "source": csrc}

    # 지원가능 전공(SKKU): 시트 E 그대로
    major_skku = sheet.get("major_skku")

    # 해외수학전공: 보일러플레이트 아니면 시트 F, 맞으면 Solar 요약
    f = sheet.get("major_abroad") or ""
    if config.MAJOR_ABROAD_BOILERPLATE in f:
        mval, msrc, _ = pick(ex.get("major_abroad_summary", {}))
        if not mval:
            mval, msrc = "교환학생 수용 전 학과(대학 홈페이지/팩트시트 확인 필요)", config.SRC_UNKNOWN
    else:
        mval, msrc = f, config.SRC_SHEET
    major_abroad = {"value": mval, "source": msrc}

    # 최소 GPA: Solar 우선, 없으면 시트 N이 GPA꼴이면 사용, 끝내 없으면 이메일 문의
    gval, gsrc, _ = pick(ex.get("gpa_min", {}))
    if not gval:
        n = sheet.get("gpa_min")
        if looks_like_gpa(n):
            gval, gsrc = n, config.SRC_SHEET
        elif n and re.search(r"n/?a|없", str(n), re.I):
            gval, gsrc = "제한 없음/명시 없음", config.SRC_SHEET
        elif email:
            gval, gsrc = config.EMAIL_INQUIRY_TEXT, config.SRC_EMAIL
        else:
            gval, gsrc = "확인필요", config.SRC_UNKNOWN
    gpa = {"value": gval, "source": gsrc}

    # 어학요건
    lval, lsrc, _ = pick(ex.get("language_requirements", {}))
    if not lval:
        j = sheet.get("language_req")
        j_clean = clean_or_email(j, email) if (j and not is_url_only(j)) else None
        if j_clean == config.EMAIL_INQUIRY_TEXT:
            lval, lsrc = j_clean, config.SRC_EMAIL
        elif j_clean and j_clean != "확인필요":
            lval, lsrc = j_clean[:120], config.SRC_SHEET
        elif email:
            lval, lsrc = config.EMAIL_INQUIRY_TEXT, config.SRC_EMAIL
        else:
            lval, lsrc = "확인필요(링크 참조)", config.SRC_UNKNOWN
    lang_req = {"value": lval, "source": lsrc}

    # 수업 언어
    ival, isrc, _ = pick(ex.get("language_of_instruction", {}))
    if not ival:
        ival, isrc = "확인필요", config.SRC_UNKNOWN
    # 혼합/현지어 → 구체적 언어명 표기 (예: "일본어, 영어")
    ival = lang_map.normalize(ival, rec["country"], (loc or {}).get("city", ""))
    lang_inst = {"value": ival, "source": isrc}

    # 위치
    loc_text = loc.get("text") if loc else None
    location_obj = {"value": loc_text or "확인필요",
                    "source": config.SRC_AI if loc_text else config.SRC_UNKNOWN,
                    "city": (loc or {}).get("city", ""),
                    "tier": (loc or {}).get("tier", ""),
                    "setting": (loc or {}).get("setting", ""),
                    "commute_min": (loc or {}).get("commute_min"),
                    "city_size": (loc or {}).get("city_size", "")}

    return {
        "country": rec["country"],
        "university": rec["university"],
        "campus": campus,
        "major_skku": major_skku,
        "major_abroad": major_abroad,
        "gpa_min": gpa,
        "semesters": clean_or_email(norm_semesters(sheet.get("semesters")), email),
        "credits_min": clean_or_email(sheet.get("credits_min"), email),
        "credits_max": clean_or_email(sheet.get("credits_max"), email),
        "location": location_obj,
        "lang_instruction": lang_inst,
        "lang_req": lang_req,
        "email": sheet.get("email"),
        "program_link": sheet.get("program_link") or (rec["links"][0]["url"] if rec["links"] else None),
        "_extract": ex,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=None)
    ap.add_argument("--country", default="UNITED STATES")
    ap.add_argument("--all", action="store_true", help="전 국가(221개) 처리")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-crawl", action="store_true")
    ap.add_argument("--out", default=None, help="data.json 경로")
    args = ap.parse_args()

    country = None if args.all else args.country
    recs = loader.load(args.xlsx, country=country, limit=args.limit)

    # 수동 오버라이드 링크 병합(비공개 팩트시트 대체 URL 등)
    overrides = config.load_overrides()
    for rec in recs:
        ov = overrides.get(rec["university"])
        if ov and ov.get("extra_links"):
            extra = [{"url": u, "col": "override"} for u in ov["extra_links"]]
            existing = {l["url"] for l in rec["links"]}
            rec["links"] = extra + [l for l in rec["links"] if l["url"] not in existing]

    print(f"[load] {country or '전체'}: {len(recs)}개 대학", flush=True)

    out_path = args.out or os.path.join(config.HERE, "data.json")
    results = []
    for i, rec in enumerate(recs, 1):
        uni = rec["university"]
        print(f"[{i}/{len(recs)}] {uni}", flush=True)
        # 1) 크롤
        sources = []
        if not args.no_crawl:
            try:
                sources = fetcher.fetch_record(rec)
                ok = sum(1 for s in sources if s.get("ok"))
                print(f"    크롤 {ok}/{len(sources)} 성공", flush=True)
            except Exception as e:
                print(f"    크롤 오류: {e}", flush=True)
        # 2) Solar 추출
        try:
            ex = extract.extract_fields(rec, sources)
        except Exception as e:
            print(f"    추출 오류: {e}", flush=True)
            ex = {}
        # 3) 위치
        try:
            loc = location.estimate(uni, rec["country"], rec["sheet"].get("campus"))
        except Exception as e:
            print(f"    위치 오류: {e}", flush=True)
            loc = None
        results.append(build_record(rec, ex, loc))
        fetcher.save_cache()
        # 체크포인트: 진행분을 주기적으로 저장(중단 대비)
        if i % 5 == 0 or i == len(recs):
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[done] {len(results)}개 → {out_path}", flush=True)

    # 표 + 사이트 빌드
    try:
        import build_table, build_site
        build_table.build(results)
        build_site.build(results)
    except Exception as e:
        print(f"[build] 출력 생성 오류: {e}", flush=True)


if __name__ == "__main__":
    main()

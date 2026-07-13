"""특징 재생성: 한국인 교환학생이 매력을 느낄 주관적 특징 위주 (2026-07-13 사용자 요청).

- 기존 특징 중 기숙사 관련(근거 기반)은 유지
- 나머지는 Solar 지식 기반 주관 특징 2~3개로 교체 (라벨=AI추정)
사용법: python refresh_features.py [--limit N] [--resume]
실행 후: python build_site.py && python build_table.py
"""
import argparse
import io
import json
import re
import sys

import solar

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SYSTEM = (
    "너는 교환학생 경험이 많은 한국인 선배다. 한국 대학생이 교환교를 고를 때 "
    "매력을 느낄 만한 그 대학·도시의 특징을 주관적이지만 사실에 기반해 알려준다. "
    "확실하지 않은 것은 쓰지 않는다. 지정한 JSON 스키마로만 답하라."
)

GUIDE = """
JSON 스키마:
{"traits": ["특징1", "특징2", "특징3"]}

한국인 교환학생 관점에서 매력적인 특징 2~3개. 각 12~28자, 명사형으로 끝내기.
좋은 예시(이 대학에 실제 해당할 때만 — 지어내지 말 것):
- "캠퍼스 주변 상권 발달해 놀거리·먹거리 풍부"
- "대학 상징인 유명 건축물·아름다운 캠퍼스"
- "현대적인 도서관·학습 시설"
- "시내로 나가는 대중교통 편리"
- "버디 프로그램 등 현지 학생과 교류 활발"
- "한국어학과가 있어 한국에 관심 있는 현지 학생과 교류 기회"
- "기숙사 1인실 위주로 쾌적"
- "유럽 한복판이라 주말 배낭여행 거점으로 최적"
- "물가 저렴해 생활비 부담 적은 편"
- "바다와 가까운 휴양 도시 분위기"
- "고즈넉한 유럽 대학도시 낭만"
- "한국인에게 인지도 높은 명문"
- "미식과 카페 문화로 유명한 도시"
- "대도시라 인턴·문화생활 기회 풍부"
규칙:
- 그 도시·대학에 실제로 해당하는 것만. 어느 도시에나 붙는 말("살기 좋음") 금지.
- [이미 있는 실용 정보]와 중복되는 내용 금지 — 제도·행정 정보(학사일정, 셔틀버스, 지원 프로그램) 말고
  도시의 분위기·여행·물가·자연·음식·명성 같은 '가서 살아보는 매력'을 우선할 것.
- 검증 불가한 주장 금지: 한국인 유학생 수, 한인 커뮤니티 규모, 구체적 순위 숫자.
- 물가·치안·날씨는 일반적으로 알려진 사실 수준에서만.
- 과장·광고 문구 금지. 단점 언급도 가치 있으면 허용(예: "물가 비싸지만 알프스 접근성 최고").
"""

_BAD = ("살기 좋", "좋은 대학", "훌륭한", "최고의 대학", "명문 대학입니다", "한국인 유학생", "한인 커뮤니티")


def _valid(t):
    if not isinstance(t, str):
        return False
    t = re.sub(r"\s+", " ", t).strip()
    return 8 <= len(t) <= 32 and not any(b in t for b in _BAD)


def gen(rec):
    loc = rec.get("location", {})
    user = (
        f"대학명: {rec['university']}\n국가: {rec['country']}\n"
        f"도시: {loc.get('city','')} ({loc.get('tier','')}, {val(rec.get('location'))})\n"
        f"[이미 있는 실용 정보 — 중복 금지]: {' / '.join(f['text'] for f in rec.get('features') or []) or '(없음)'}\n\n" + GUIDE
    )
    out = solar.chat_json(SYSTEM, user)
    traits = [re.sub(r"\s+", " ", t).strip() for t in (out.get("traits") or []) if _valid(t)]
    return traits[:3]


def val(o):
    return (o.get("value") if isinstance(o, dict) else o) or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true", help="_subj 마커 있는 학교 건너뛰기")
    args = ap.parse_args()

    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    targets = data[: args.limit] if args.limit else data
    for i, rec in enumerate(targets, 1):
        if args.resume and rec.get("_subj"):
            continue
        keep = [f for f in (rec.get("features") or []) if "기숙사" in f["text"]]
        try:
            traits = gen(rec)
        except Exception as e:
            print(f"[{i}/{len(targets)}] {rec['university']}: 오류 {e}", flush=True)
            continue
        rec["features"] = keep + [{"text": t, "source": "AI추정"} for t in traits]
        rec["_subj"] = True
        print(f"[{i}/{len(targets)}] {rec['university']}: "
              + " · ".join(f["text"] for f in rec["features"]), flush=True)
        if i % 10 == 0:
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    n = sum(1 for r in data if r.get("_subj"))
    print(f"\n완료: {n}/{len(data)}개교")


if __name__ == "__main__":
    main()

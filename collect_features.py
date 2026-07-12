"""특징 변수 수집: 시트 추가정보(X) + 크롤 캐시 원문 + 규칙 기반 → data.json rec['features'].

사용법:
  python collect_features.py --limit 5    # 시험
  python collect_features.py              # 전체
  python collect_features.py --resume     # 이미 features 있는 학교 건너뛰기
실행 후: python build_table.py && python build_site.py
"""
import argparse
import collections
import io
import json
import sys

import extract
import features
import fetcher
import loader

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = "data.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    by_name = {r["university"]: r for r in data}

    sheet_recs = loader.load()
    targets = sheet_recs[: args.limit] if args.limit else sheet_recs
    done = 0
    for i, srec in enumerate(targets, 1):
        drec = by_name.get(srec["university"])
        if drec is None:
            print(f"[{i}] {srec['university']}: data.json에 없음 — 건너뜀")
            continue
        if args.resume and drec.get("features"):
            continue
        try:
            sources = fetcher.fetch_record(srec)
        except Exception as e:
            print(f"[{i}] {srec['university']}: 크롤 오류 {e}")
            sources = []
        sources_text = extract._sources_block(sources or [])
        if sources_text.startswith("(크롤링된 원문 없음"):
            sources_text = ""
        try:
            feats = features.collect(drec, srec["sheet"].get("additional"), sources_text)
        except Exception as e:
            print(f"[{i}/{len(targets)}] {srec['university']}: 추출 오류 {e}")
            feats = features.rule_features(drec)
        drec["features"] = feats
        done += 1
        shown = " · ".join(f"{f['text']}[{f['source']}]" for f in feats) or "(없음)"
        print(f"[{i}/{len(targets)}] {srec['university']}: {shown}", flush=True)
        if i % 10 == 0:
            with open(DATA, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            fetcher.save_cache()

    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    fetcher.save_cache()

    c = collections.Counter()
    for r in data:
        for ftr in r.get("features") or []:
            c[ftr["source"]] += 1
    n_has = sum(1 for r in data if r.get("features"))
    print(f"\n처리 {done}건 · features 보유 {n_has}/{len(data)}개교 · 출처 분포 {dict(c)}")


if __name__ == "__main__":
    main()

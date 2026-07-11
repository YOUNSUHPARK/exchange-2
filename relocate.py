"""data.json의 위치만 3단계 분류로 재추정 (크롤/추출 재실행 없음).

사용법:
  python relocate.py --limit 5   # 시험 실행 (앞 5개교만)
  python relocate.py             # 전체 221개교
갱신 후: python build_table.py && python build_site.py
"""
import argparse
import collections
import io
import json
import sys

import config
import location

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA = "data.json"


def campus_hint(rec):
    c = rec.get("campus")
    if isinstance(c, dict):
        v = c.get("value")
    else:
        v = c
    if v and v not in ("확인필요",):
        return v
    return None


def reclassify(data):
    """Solar 재호출 없이, 저장된 사실값으로 tier만 재계산해 라벨 교체."""
    changed = 0
    for rec in data:
        l = rec.get("location", {})
        if not l.get("city_size"):
            continue
        tier = location.classify_tier(l["city_size"], l.get("commute_min") or 0,
                                      l.get("major_city_min"))
        if tier != l.get("tier"):
            old_value = l.get("value", "")
            desc = old_value.split(" — ", 1)[1] if " — " in old_value else old_value
            l["value"] = f"{tier} — {desc}"
            print(f"  {rec['university']}: {l.get('tier')} → {tier} ({desc})")
            l["tier"] = tier
            l["setting"] = tier
            changed += 1
    print(f"재분류 변경: {changed}건")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="앞 N개교만 (시험용)")
    ap.add_argument("--resume", action="store_true",
                    help="이미 tier가 있는 학교는 건너뛰기 (중단 후 이어서)")
    ap.add_argument("--reclassify", action="store_true",
                    help="Solar 호출 없이 저장된 사실값으로 tier만 재계산")
    args = ap.parse_args()

    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    if args.reclassify:
        data = reclassify(data)
        with open(DATA, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        dist = collections.Counter(r["location"].get("tier", "") for r in data)
        print("=== 3단계 분포 ===")
        for k, v in dist.most_common():
            print(f"  {k or '(확인필요)'}: {v}")
        return

    targets = data[: args.limit] if args.limit else data
    if args.resume:
        targets = [r for r in targets if not r.get("location", {}).get("tier")]
    print(f"위치 재추정 대상: {len(targets)}개교")

    fails = []
    for i, rec in enumerate(targets, 1):
        uni = rec["university"]
        try:
            loc = location.estimate(uni, rec["country"], campus_hint(rec))
        except Exception as e:
            print(f"[{i}/{len(targets)}] {uni}: 오류 {e}", flush=True)
            loc = None
        if loc:
            rec["location"] = {
                "value": loc["text"],
                "source": config.SRC_AI,
                "city": loc["city"],
                "tier": loc["tier"],
                "setting": loc["setting"],
                "commute_min": loc["commute_min"],
                "major_city_min": loc.get("major_city_min"),
                "city_size": loc["city_size"],
                "transport": loc.get("transport", ""),
                "major_city_note": loc.get("major_city_note", ""),
            }
            print(f"[{i}/{len(targets)}] {uni}: {loc['text']}", flush=True)
        else:
            rec["location"] = {"value": "확인필요", "source": config.SRC_UNKNOWN,
                               "city": "", "tier": "", "setting": "",
                               "commute_min": None, "city_size": ""}
            fails.append(uni)
            print(f"[{i}/{len(targets)}] {uni}: 확인필요(형식 검증 실패)", flush=True)
        if i % 10 == 0:  # 중간 저장
            with open(DATA, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)

    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    dist = collections.Counter(r["location"].get("tier", "") for r in targets)
    print("\n=== 3단계 분포 ===")
    for k, v in dist.most_common():
        print(f"  {k or '(확인필요)'}: {v}")
    if fails:
        print(f"검증 실패 {len(fails)}건: {', '.join(fails)}")


if __name__ == "__main__":
    main()

"""수업언어 정확도 개선 일괄 적용 (2026-07-12, 공식 페이지 검증 기반).

1) 웹 검증한 25개교(확인필요 7 + 현지어 18) + York → VERIFIED 값으로 교체 (source=웹)
2) 나머지 '혼합'/'현지어' → lang_map으로 "현지어명, 영어"/"현지어명" 표기 변환 (source 유지)
실행 후: python build_table.py && python build_site.py
"""
import io
import json
import sys

import lang_map

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 공식 페이지/공식 factsheet 확인 결과 (근거는 커밋 메시지·세션 기록 참조)
VERIFIED = {
    # 확인필요 7곳
    "Renmin Business School, Renmin University of China": "영어",   # 교환학생은 영어강의만 수강
    "Leuphana University Luneburg": "독일어, 영어",
    "Gadjah Mada University (UGM)": "인도네시아어, 영어",
    "Polytechnic University of Milan": "이탈리아어, 영어",          # 학부 이탈리아어, 석사 영어
    "Daito Bunka University": "일본어",                             # 교환은 일본어·일본문화 과정 중심
    "KIMEP University": "영어",                                     # 영어 단일 교육
    "Istanbul Technical University": "터키어, 영어",                # 100% 영어 프로그램 보유(E코드)
    # 현지어 18곳 검증 결과 — 영어강의 실재 확인 → 혼합으로 정정
    "University of Vienna": "독일어, 영어",
    "Shanghai Jiao Tong University": "중국어, 영어",
    "National Chengchi University": "중국어, 영어",                 # 연 500+ 영어강의
    "University of Pecs": "헝가리어, 영어",
    "INSEEC Business School": "프랑스어, 영어",
    "Chuo University": "일본어, 영어",                              # 영어강의 수강 시 일본어 불요
    "Hacettepe University": "터키어, 영어",                         # 영어 매체 학과 존재(B1 영어)
    # 현지어 판정이 맞았던 곳 → 구체적 언어명으로 표기
    "Unisinos University": "포르투갈어",
    "University of Sao Paulo": "포르투갈어",
    "UNICAMP (University of Campinas)": "포르투갈어",
    "Universite du Quebec a Montreal(UQAM)": "프랑스어",            # 지원에 프랑스어 필수(ESG 영어 소수)
    "University of Montreal": "프랑스어",                           # 프랑스어 B2 필수
    "National Institute for Oriental Languages and Civilizations (INALCO)": "프랑스어",
    "Nishogakusha University": "일본어",
    "Fukuoka University": "일본어",                                 # 정규수업 JLPT N2 필요
    "Dokkyo University": "일본어",                                  # 일본어 프로그램 필수
    "Pontifical Catholic University of Peru": "스페인어",           # 영어강의 소수, 스페인어 요구
    "Polytechnic University of Valencia": "스페인어",               # 영어강의 정원 제한적, 스페인어 B1
    # 혼합이었지만 실제로는 영어권 대학
    "York University": "영어, 프랑스어",                            # 메인 영어, 글렌던 캠퍼스 이중언어
}
VERIFIED = {k: v for k, v in VERIFIED.items() if v}


def main():
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    n_ver, n_conv, unchanged = 0, 0, []
    for rec in data:
        li = rec["lang_instruction"]
        old = li["value"]
        if rec["university"] in VERIFIED:
            li["value"] = VERIFIED[rec["university"]]
            li["source"] = "웹"
            n_ver += 1
            print(f"[검증] {rec['university']}: {old} → {li['value']}")
        elif old in ("혼합", "현지어"):
            new = lang_map.normalize(old, rec["country"], rec["location"].get("city", ""))
            if new != old:
                li["value"] = new
                n_conv += 1
            else:
                unchanged.append(rec["university"])

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"\n검증 반영 {n_ver}건, 표기 변환 {n_conv}건")
    if unchanged:
        print(f"변환 불가(매핑 없음) {len(unchanged)}건: {', '.join(unchanged)}")


if __name__ == "__main__":
    main()

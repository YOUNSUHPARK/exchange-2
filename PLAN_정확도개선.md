# 정확도 개선 계획 — 수작업 검수 + 재추출 (다음 세션용)

작성: 2026-07-11. 전체 221개교 1차 항목화 완료 후, **어학요건부터 세부사항을 수작업으로 교정**하기 위한 계획.

## 현재 상태
- `data.json` = 원천 데이터(221개교, 출처·근거 포함) → `out/universities.csv·xlsx`, `out/index.html` 자동 생성
- `review_checklist.csv` = **자동 스캔한 이상 항목 목록 (113개교, 167건)** ← 여기서부터 시작
  - 너무 김 73 · 점수 없는 문장 31 · 미확보 21 · 어학요건 장문 15 · URL만 10 · GPA 문장형 9 · 전공 장문 4 · subscore 의심 4

## 작업 순서 (우선순위)

### 1단계: 어학요건 (가장 먼저, 사용자 지정)
`review_checklist.csv`에서 항목=어학요건 필터 후 유형별 처리:
- **subscore 의심 4건** (예: "IELTS 5.5+"가 실제론 밴드 최소치, "iBT 4+" 등) → 대학 공식 페이지에서 overall 점수 확인 → 수정
- **너무 김 15건** → "TOEFL iBT NN+, IELTS N.N+" 형식으로 압축 (부수 시험 삭제)
- **URL만/점수 없음 41건** → URL 방문해 점수 찾기. 있으면 기입, 진짜 없으면(홈교 위임 등) "요건 없음(홈교 기준)" 또는 "담당자 이메일 문의"
- **미확보** → 프로그램 홈페이지 → factsheet → 그래도 없으면 이메일문의 표기 유지

### 2단계: 최소 GPA
- 문장형 9건 → "N.N/4.0" 형식으로 정규화 (스케일 표기 유지)
- URL만 → 방문해 확인

### 3단계: 학점/학기/전공/캠퍼스
- 최소·최대학점 "너무 김" → 숫자+단위만 남기기 (예: "12~18 credits", "30 ECTS")
- 해외수학전공 장문 4건 → 학부단위 개방여부 한 줄 요약
- 수업언어 확인필요 7건 → 대학 페이지에서 영어강의 목록 유무 확인

## 수정 방법 (두 가지)

**A. 값 직접 수정** — `overrides.json`에 `"대학명": {"fields": {"lang_req": "TOEFL iBT 80+, IELTS 6.0+", ...}}` 형태로 추가.
⚠️ 현재 run.py는 `extra_links`만 반영하고 `fields` 직접 주입은 **미구현** → 다음 세션에서 먼저 구현할 것 (build_record 마지막에 overrides의 fields를 최우선으로 덮어쓰고 source="수동확인" 라벨 추가).

**B. 공개 URL 제공** — `overrides.json`의 `extra_links`에 URL 추가 후 해당 대학만 재추출 (Boise State 사례 참조: rec["links"] 앞에 붙이고 extract → data.json 교체 → build).

수정 후 반드시: `python build_table.py && python build_site.py` (data.json에서 재생성).

## 검증 루프
1. 수정한 대학은 index.html에서 열어 눈으로 확인
2. 스캔 스크립트 재실행해 이상 건수 감소 확인 (이 파일 하단 스크립트 참조 — review_checklist.csv 생성 로직은 이번 세션 대화 기록/스크립트에 있음. 필요하면 `audit.py`로 저장해 둘 것)
3. 목표: subscore 의심 0건, URL만 0건, "너무 김" 유형은 90자 이내로

## 주의사항
- **비공개 구글드라이브 factsheet는 자동수집 불가** (로그인 필요) → 사용자가 직접 열어 값을 알려주거나 공개 URL로 대체
- Solar가 스키마 옵션 문자열("영어|현지어|혼합")을 복사하는 버그 있었음 → 수정됨. 재추출 시 '|' 포함 값 나오면 같은 문제
- 근거 없는 값은 절대 임의로 채우지 말 것 — "확인필요"/"이메일문의" 유지가 원칙
- API 키: `exchange 2\exchange api key.txt` (Solar/Upstage, config.py가 자동 로드)

"""공통 설정: 시트 컬럼 매핑, Solar API 설정, 경로."""
import os

# universities.xlsx 위치 (기본: 옆 exchange 폴더). 필요 시 run.py --xlsx 로 덮어씀.
DEFAULT_XLSX = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "exchange", "universities.xlsx",
)

HEADER_ROW = 6          # 실제 헤더가 있는 행
FIRST_DATA_ROW = 7

# 시트 컬럼(엑셀 문자) → 의미
COL = {
    "country": "A",
    "university": "B",
    "campus_count": "C",
    "campus": "D",              # 지원가능 캠퍼스
    "major_skku": "E",          # 지원 가능 전공(우리 대학 기준)
    "major_abroad": "F",        # 해외대학 수학 전공
    "quota": "G",
    "email": "H",
    "program_link": "I",
    "language_req": "J",        # 어학 요건
    "grad": "K",
    "one_year": "L",
    "outside_major": "M",
    "gpa_min": "N",             # 최소 GPA
    "semesters": "O",           # 가을학기까지 마쳐야 하는 학기 수
    "credits_min": "P",
    "credits_max": "Q",
    "nomination_deadline": "R",
    "application_deadline": "S",
    "major_restrict": "T",
    "course_restrict": "U",
    "catalog": "V",
    "factsheet": "W",           # 대개 구글드라이브
    "additional": "X",
}

# 링크를 수집할 컬럼(크롤링 대상 우선순위)
LINK_COLUMNS = ["program_link", "gpa_min", "language_req", "campus", "factsheet", "catalog", "major_abroad", "additional"]

# 해외전공 F열 보일러플레이트(이 문구면 크롤링해서 학부단위 요약)
MAJOR_ABROAD_BOILERPLATE = "교환학생 수용하는 모든 학과"

# ---- Solar (Upstage) ----
def _load_dotenv():
    """프로젝트 폴더의 .env(있으면)를 환경변수처럼 로드. 키를 코드/채팅에 남기지 않기 위함."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv()

SOLAR_BASE_URL = os.environ.get("SOLAR_BASE_URL", "https://api.upstage.ai/v1")
SOLAR_MODEL = os.environ.get("SOLAR_MODEL", "solar-pro2")

# 키를 담아둘 수 있는 파일들(코드/채팅에 노출 안 함). 파일 내용에 up-... 토큰만 있으면 됨.
_KEY_FILES = ["exchange api key.txt", "solar_key.txt", "api_key.txt"]

def _read_key_file():
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    for fn in _KEY_FILES:
        p = os.path.join(here, fn)
        if os.path.exists(p):
            # BOM 대응 위해 utf-8-sig
            raw = open(p, encoding="utf-8-sig", errors="ignore").read().strip()
            # KEY=값 형태면 값만, 아니면 up- 토큰 추출
            if "=" in raw and "up-" in raw.split("=", 1)[1]:
                raw = raw.split("=", 1)[1].strip().strip('"').strip("'")
            m = re.search(r"up-[A-Za-z0-9._-]+", raw)
            if m:
                return m.group(0)
            if raw:
                return raw
    return None

def solar_api_key():
    return (os.environ.get("SOLAR_API_KEY") or os.environ.get("UPSTAGE_API_KEY")
            or _read_key_file())

# ---- 경로 ----
HERE = os.path.dirname(os.path.abspath(__file__))
CRAWL_CACHE = os.path.join(HERE, "crawl_cache.json")   # url -> {text, kind, ok, error}
OUT_DIR = os.path.join(HERE, "out")

# 출처/신뢰도 라벨
SRC_SHEET = "시트"
SRC_WEB = "웹"
SRC_FACTSHEET = "factsheet"
SRC_AI = "AI추정"
SRC_UNKNOWN = "확인필요"
SRC_EMAIL = "이메일문의"          # 시트·웹·팩트시트 어디에도 없어 담당자 문의 필요

EMAIL_INQUIRY_TEXT = "담당자 이메일 문의"

# 수동 오버라이드(비공개 팩트시트 등으로 자동수집이 안 되는 대학): 대학명 → {extra_links:[...], fields:{...}}
OVERRIDES = os.path.join(HERE, "overrides.json")

def load_overrides():
    import json
    if os.path.exists(OVERRIDES):
        with open(OVERRIDES, encoding="utf-8") as f:
            return json.load(f)
    return {}

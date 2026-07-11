"""견고한 링크 크롤러: URL → 정제된 원문 텍스트. 결과를 crawl_cache.json에 저장(증분).

- 브라우저 User-Agent/헤더로 403 최소화, 재시도+백오프
- HTML: BeautifulSoup 본문 텍스트
- PDF: pypdf 텍스트 추출
- Google Drive(open?id / file/d): 로그인 없이 직접 다운로드 후 형식 감지
- 실패 사유를 캐시에 기록(확인필요 표기용)
"""
import io
import json
import os
import re
import time
import requests
import config

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None
try:
    import pypdf
except Exception:
    pypdf = None

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}
TIMEOUT = 25
MAX_TEXT = 20000        # 소스당 저장 텍스트 상한
_cache = None


def _load_cache():
    global _cache
    if _cache is None:
        if os.path.exists(config.CRAWL_CACHE):
            with open(config.CRAWL_CACHE, encoding="utf-8") as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache


def save_cache():
    if _cache is not None:
        tmp = config.CRAWL_CACHE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False)
        os.replace(tmp, config.CRAWL_CACHE)


def _drive_id(url):
    m = re.search(r"/file/d/([\w-]+)", url) or re.search(r"[?&]id=([\w-]+)", url)
    return m.group(1) if m else None


def _extract_pdf(data):
    if not pypdf:
        return None, "pypdf 미설치"
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        text = text.strip()
        return (text, None) if text else (None, "PDF 텍스트 없음(스캔본 가능)")
    except Exception as e:
        return None, f"PDF 파싱 오류: {e}"


def _extract_html(content, encoding=None):
    if not BeautifulSoup:
        return content[:MAX_TEXT], None
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text, None


def _fetch_drive(url):
    fid = _drive_id(url)
    if not fid:
        return None, None, "드라이브 ID 추출 실패"
    dl = f"https://drive.google.com/uc?export=download&id={fid}"
    with requests.Session() as s:
        r = s.get(dl, headers=HEADERS, timeout=TIMEOUT, stream=True)
        # 대용량 바이러스 스캔 확인 페이지 통과
        if "text/html" in r.headers.get("Content-Type", ""):
            token = None
            for k, v in r.cookies.items():
                if k.startswith("download_warning"):
                    token = v
            m = re.search(r"confirm=([\w-]+)", r.text)
            if m:
                token = m.group(1)
            if token:
                r = s.get(dl + f"&confirm={token}", headers=HEADERS, timeout=TIMEOUT)
        data = r.content
    return _sniff_bytes(data)


def _sniff_bytes(data):
    """바이트 형식 감지 → (text, kind, error)."""
    if data[:4] == b"%PDF":
        text, err = _extract_pdf(data)
        return text, "pdf", err
    if data[:2] == b"PK":  # zip = docx/pptx/xlsx
        text, err = _extract_zip_office(data)
        return text, "office", err
    # 그 외는 HTML/텍스트로 시도
    try:
        text, _ = _extract_html(data)
        return text, "html", None
    except Exception as e:
        return None, "unknown", f"형식 감지 실패: {e}"


def _extract_zip_office(data):
    import zipfile
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        chunks = []
        for name in z.namelist():
            if name.endswith(".xml") and ("document" in name or "slide" in name):
                raw = z.read(name).decode("utf-8", "ignore")
                chunks.append(re.sub(r"<[^>]+>", " ", raw))
        text = re.sub(r"\s+", " ", " ".join(chunks)).strip()
        return (text, None) if text else (None, "office 텍스트 없음")
    except Exception as e:
        return None, f"office 파싱 오류: {e}"


def fetch(url, force=False):
    """URL 하나를 가져와 정제 텍스트 반환. 캐시 사용."""
    cache = _load_cache()
    if not force and url in cache:
        return cache[url]

    result = {"url": url, "text": None, "kind": None, "ok": False, "error": None}
    try:
        if "drive.google.com" in url or "docs.google.com" in url:
            text, kind, err = _fetch_drive(url)
        else:
            last = None
            for attempt in range(3):
                try:
                    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                    r.raise_for_status()
                    ct = r.headers.get("Content-Type", "")
                    if "pdf" in ct or r.content[:4] == b"%PDF":
                        text, err = _extract_pdf(r.content)
                        kind = "pdf"
                    else:
                        text, err = _extract_html(r.content)
                        kind = "html"
                    last = None
                    break
                except Exception as e:
                    last = e
                    time.sleep(1.5 * (attempt + 1))
            if last is not None:
                raise last
        if text:
            result.update(text=text[:MAX_TEXT], kind=kind, ok=True, error=err)
        else:
            result.update(kind=kind, ok=False, error=err or "빈 텍스트")
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"[:200]

    cache[url] = result
    return result


def fetch_record(rec, max_links=5):
    """레코드의 링크들을 우선순위대로 가져와 소스 목록 반환."""
    sources = []
    for link in rec["links"][:max_links]:
        res = fetch(link["url"])
        res = dict(res)
        res["col"] = link["col"]
        sources.append(res)
        time.sleep(0.5)
    return sources

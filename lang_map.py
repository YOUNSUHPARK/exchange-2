"""국가 → 현지어(한국어 표기) 매핑 + 수업언어 값 정규화.

'혼합' → "현지어명, 영어", '현지어' → "현지어명"으로 구체화한다 (사용자 지정 표기).
다언어 국가(캐나다·스위스·벨기에)는 소재 도시로 판별.
"""

COUNTRY_LANG = {
    "AUSTRALIA": "영어", "AUSTRIA": "독일어", "BRAZIL": "포르투갈어",
    "CHINA": "중국어", "CROATIA": "크로아티아어", "CZECH REPUBLIC": "체코어",
    "DENMARK": "덴마크어", "ECUADOR": "스페인어", "ESTONIA": "에스토니아어",
    "FINLAND": "핀란드어", "FRANCE": "프랑스어", "GERMANY": "독일어",
    "HONG KONG": "중국어", "HUNGARY": "헝가리어", "INDONESIA": "인도네시아어",
    "ITALY": "이탈리아어", "JAPAN": "일본어", "KAZAKHSTAN": "러시아어",
    "LITHUANIA": "리투아니아어", "MEXICO": "스페인어", "NETHERLANDS": "네덜란드어",
    "NORWAY": "노르웨이어", "PERU": "스페인어", "POLAND": "폴란드어",
    "PORTUGAL": "포르투갈어", "SINGAPORE": "영어", "SPAIN": "스페인어",
    "SWEDEN": "스웨덴어", "TAIWAN": "중국어", "THAILAND": "태국어",
    "TURKEY": "터키어", "UNITED KINGDOM": "영어", "UNITED STATES": "영어",
    "VIET NAM": "베트남어",
}

# 다언어 국가: 도시명(한국어 표기)에 아래 키워드가 포함되면 해당 언어
CITY_LANG = {
    "CANADA": ([("몬트리올", "프랑스어"), ("퀘벡", "프랑스어"), ("셔브룩", "프랑스어")], "영어"),
    "SWITZERLAND": ([("제네바", "프랑스어"), ("로잔", "프랑스어"), ("뇌샤텔", "프랑스어"),
                     ("프리부르", "프랑스어"), ("루가노", "이탈리아어")], "독일어"),
    "BELGIUM": ([("겐트", "네덜란드어"), ("안트베르펜", "네덜란드어"), ("앤트워프", "네덜란드어"),
                 ("루뱅", "네덜란드어")], "프랑스어"),
}


def local_lang(country, city=""):
    """국가(+도시)의 현지어. 모르면 None."""
    if country in CITY_LANG:
        rules, default = CITY_LANG[country]
        for kw, lang in rules:
            if kw in (city or ""):
                return lang
        return default
    return COUNTRY_LANG.get(country)


def normalize(value, country, city=""):
    """수업언어 값 정규화: 혼합/현지어를 구체적 언어명으로. 못 바꾸면 원래 값 유지."""
    lang = local_lang(country, city)
    if not lang:
        return value
    if value == "혼합":
        return "영어" if lang == "영어" else f"{lang}, 영어"
    if value == "현지어":
        return lang
    return value

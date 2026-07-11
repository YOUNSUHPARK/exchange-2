"""Upstage Solar API 클라이언트 (OpenAI 호환). JSON 강제 + 재시도."""
import json
import time
from openai import OpenAI
import config

_client = None


def client():
    global _client
    if _client is None:
        key = config.solar_api_key()
        if not key:
            raise RuntimeError(
                "SOLAR_API_KEY(또는 UPSTAGE_API_KEY) 환경변수가 없습니다. "
                "터미널에서 `export SOLAR_API_KEY=up-...` 후 다시 실행하세요."
            )
        _client = OpenAI(api_key=key, base_url=config.SOLAR_BASE_URL)
    return _client


def chat_json(system, user, model=None, temperature=0.0, retries=3):
    """system/user 프롬프트로 JSON 객체를 받아 dict로 반환."""
    model = model or config.SOLAR_MODEL
    last = None
    for attempt in range(retries):
        try:
            resp = client().chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError as e:
            last = e
            # JSON 실패 시 코드펜스 제거 후 재시도
            try:
                cleaned = content.strip().strip("`")
                cleaned = cleaned[cleaned.find("{"): cleaned.rfind("}") + 1]
                return json.loads(cleaned)
            except Exception:
                pass
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Solar 호출 실패: {last}")


def ping():
    """키/연결 확인용 간단 호출."""
    out = chat_json(
        "You return JSON.",
        'Return {"ok": true} as JSON.',
    )
    return out

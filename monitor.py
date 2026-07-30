import os

import requests


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/key"
OPENROUTER_API_KEYS = [
    ("v1", "agent용 API", os.getenv("OPENROUTER_API_KEY_V1")),
    ("v2", "hermes용 API", os.getenv("OPENROUTER_API_KEY_V2")),
]
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def format_amount(value):
    return f"${value:.4f}" if isinstance(value, (int, float)) else "확인 불가"


def build_budget_embed(version, api_label, api_key):
    if not api_key:
        return {
            "title": f"⚠️ {version} | {api_label}",
            "description": f"OPENROUTER_API_KEY_{version.upper()} 환경 변수가 없습니다.",
            "color": 15105570,
        }

    try:
        response = requests.get(
            OPENROUTER_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        limit = data.get("limit")
        usage = data.get("usage")
        remaining = limit - usage if isinstance(limit, (int, float)) and isinstance(usage, (int, float)) else None

        return {
            "title": f"📌 {version} | {api_label}",
            "description": f"API 키: {data.get('label') or '기본 키'}",
            "color": 3447003,
            "fields": [
                {"name": "총 사용 금액", "value": format_amount(usage), "inline": True},
                {
                    "name": "설정된 한도",
                    "value": format_amount(limit) if limit is not None else "제한 없음",
                    "inline": True,
                },
                {
                    "name": "남은 예산",
                    "value": f"**{format_amount(remaining)}**" if remaining is not None else "제한 없음",
                    "inline": False,
                },
            ],
        }
    except (requests.RequestException, ValueError) as error:
        return {
            "title": f"🚨 {version} | {api_label}",
            "description": f"예산 조회 실패: {error}",
            "color": 15158332,
        }


def check_budget_and_notify():
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL 환경 변수가 없습니다.")

    embeds = [
        build_budget_embed(version, api_label, api_key)
        for version, api_label, api_key in OPENROUTER_API_KEYS
    ]
    message = {
        "content": "⏰ **OpenRouter 일일 예산 리포트**",
        "embeds": embeds,
    }

    response = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=15)
    response.raise_for_status()
    print("디스코드 통합 알림 전송 성공")


if __name__ == "__main__":
    check_budget_and_notify()

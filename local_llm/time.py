import json
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

import ollama

MODEL = "llama3.2:latest"

# An LLM cannot know the current time, so we only use it to map a
# country name -> IANA timezone. Python computes the actual time.
PROMPT = """
ONLY reply with JSON in this exact format, nothing else:
{{"country": "<country name>", "timezone": "<IANA timezone of its capital city>"}}

Rules:
- Use a valid IANA timezone name such as Asia/Kolkata, Europe/Paris, America/New_York.
- If the country has multiple timezones, use the capital city's timezone.

Country: {country}
"""


def get_timezone(country: str) -> dict:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(country=country)}],
        format="json",
        options={"temperature": 0},
    )
    return json.loads(response["message"]["content"])


def get_current_time(country: str) -> str:
    data = get_timezone(country)
    tz_name = data.get("timezone", "")

    # Validate the LLM output so a wrong/hallucinated zone never gets used
    if tz_name not in available_timezones():
        raise ValueError(f"LLM returned an invalid timezone: {tz_name!r}")

    now = datetime.now(ZoneInfo(tz_name))
    return (
        f"Country   : {data.get('country', country)}\n"
        f"Timezone  : {tz_name}\n"
        f"Local time: {now.strftime('%A, %d %B %Y, %I:%M:%S %p')} ({now.tzname()}, UTC{now.strftime('%z')})"
    )


if __name__ == "__main__":
    country = input("Enter the country name: ")
    try:
        print("\n" + get_current_time(country))
    except Exception as e:
        print(f"\nCould not determine the time: {e}")

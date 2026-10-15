import json
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import ollama

MODEL = "llama3.2:latest"

SYSTEM_PROMPT = """You are a helpful assistant.
You do NOT know the current date or time. Whenever the user asks about the
current time or date anywhere in the world, you MUST call the get_current_time
tool with the correct IANA timezone (for example Asia/Kolkata, Europe/London,
America/New_York). For countries with many timezones, use the capital city's
timezone. You also do NOT know the current weather. Whenever the user asks about weather
or temperature anywhere, you MUST call the get_weather tool with a city name
(for a country, use its capital city). Never guess weather values.
For every other question, answer normally."""


# ---------- Tool (real Python code the LLM can call) ----------
def get_current_time(timezone: str) -> str:
    """Get the real current date and time for an IANA timezone.

    Args:
        timezone: IANA timezone name, e.g. Asia/Kolkata, Europe/London, America/New_York

    Returns:
        The current local date and time in that timezone.
    """
    try:
        now = datetime.now(ZoneInfo(timezone))
    except (ZoneInfoNotFoundError, ValueError):
        return f"Error: '{timezone}' is not a valid IANA timezone. (On Windows run: pip install tzdata)"
    return now.strftime(f"%A, %d %B %Y, %I:%M:%S %p ({timezone}, UTC%z)")


WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_weather(location: str) -> str:
    """Get the real current weather for a city.

    Args:
        location: City name, e.g. Chennai, London, Tokyo. For a country, pass its capital city.

    Returns:
        Current temperature, feels-like, humidity, wind and sky condition.
    """
    try:
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode({"name": location, "count": 1})
        )
        results = _get_json(geo_url).get("results")
        if not results:
            return f"Error: could not find a place named '{location}'."
        place = results[0]

        weather_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
            "timezone": "auto",
        })
        cur = _get_json(weather_url)["current"]
    except Exception as e:
        return f"Error fetching weather: {e}"

    name = f"{place['name']}, {place.get('country', '')}".strip(", ")
    sky = WEATHER_CODES.get(cur["weather_code"], "Unknown")
    return (
        f"Weather in {name}: {sky}, {cur['temperature_2m']}°C "
        f"(feels like {cur['apparent_temperature']}°C), "
        f"humidity {cur['relative_humidity_2m']}%, wind {cur['wind_speed_10m']} km/h."
    )


AVAILABLE_TOOLS = {"get_current_time": get_current_time, "get_weather": get_weather}
TOOLS = [get_current_time, get_weather]


# ---------- Chat loop ----------
def ask(messages: list) -> str:
    response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
    messages.append(response.message)

    # If the LLM wants to use a tool, run it and give the result back
    while response.message.tool_calls:
        for call in response.message.tool_calls:
            func = AVAILABLE_TOOLS.get(call.function.name)
            result = func(**call.function.arguments) if func else f"Unknown tool: {call.function.name}"
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})

        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS)
        messages.append(response.message)

    return response.message.content


if __name__ == "__main__":
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Ask me anything (type 'exit' to quit)\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        messages.append({"role": "user", "content": question})
        try:
            print(f"\nAI: {ask(messages)}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

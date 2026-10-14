from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import ollama

MODEL = "llama3.2:latest"

SYSTEM_PROMPT = """You are a helpful assistant.
You do NOT know the current date or time. Whenever the user asks about the
current time or date anywhere in the world, you MUST call the get_current_time
tool with the correct IANA timezone (for example Asia/Kolkata, Europe/London,
America/New_York). For countries with many timezones, use the capital city's
timezone. For every other question, answer normally."""


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


AVAILABLE_TOOLS = {"get_current_time": get_current_time}


# ---------- Chat loop ----------
def ask(messages: list) -> str:
    response = ollama.chat(model=MODEL, messages=messages, tools=[get_current_time])
    messages.append(response.message)

    # If the LLM wants to use a tool, run it and give the result back
    while response.message.tool_calls:
        for call in response.message.tool_calls:
            func = AVAILABLE_TOOLS.get(call.function.name)
            result = func(**call.function.arguments) if func else f"Unknown tool: {call.function.name}"
            messages.append({"role": "tool", "tool_name": call.function.name, "content": str(result)})

        response = ollama.chat(model=MODEL, messages=messages, tools=[get_current_time])
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

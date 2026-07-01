import os
import random
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# a sentinel value we can detect in app.py
AI_ERROR_SENTINEL = "__AI_ERROR__"


def get_response(chat_history, system_prompt="You are a friendly and helpful chatbot called Buddy."):
    """Send the full conversation to Groq's AI and return its reply."""

    messages = [{"role": "system", "content": system_prompt}]

    for message in chat_history:
        messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"⚠️ AI API error: {e}")
        return AI_ERROR_SENTINEL   # signal failure without crashing
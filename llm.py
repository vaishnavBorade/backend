import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Define constants once
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
MODEL_NAME = "mistralai/mistral-7b-instruct"

def explain_match(jd: str, resume_text: str) -> str:
    prompt = f"""
You are an AI recruiter. Evaluate the following resume against the job description.
Give a match score (0 to 100) and a short 50-word explanation.

Job Description:
{jd}

Resume:
{resume_text}
"""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=HEADERS,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are a helpful recruiter."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=30
        )

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            print("[❌ LLM ERROR RESPONSE]", data)
            return "Score: 0\n[LLM Error: No response from AI]"

    except requests.exceptions.RequestException as e:
        print("[🔥 NETWORK EXCEPTION]", e)
        return "Score: 0\n[LLM Network Exception]"

    except Exception as e:
        print("[🔥 GENERAL EXCEPTION]", e)
        return "Score: 0\n[Unexpected error occurred]"

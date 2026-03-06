# test_groq.py
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

try:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello, Groq!"}],
        model="llama-3.3-70b-versatile",
    )
    print("接続成功！:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"接続失敗...: {e}")
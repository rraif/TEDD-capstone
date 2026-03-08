import httpx
import os
import re
from dotenv import load_dotenv

load_dotenv("../.env")

OLLAMA_URL = os.environ.get("OLLAMA_URL")
MODEL_NAME = os.environ.get("OLLAMA_MODEL")


async def call_ollama(prompt: str) -> str:
    """
    Calls local Ollama LLaMA model and returns raw text output.
    Increased timeout to handle first-time model warmup.
    """

    timeout = httpx.Timeout(300.0)  # 5 minutes

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "format": "json",  # Forces strict JSON mode in Ollama
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1500
                }
            }
        )

        if response.status_code != 200:
            raise RuntimeError(f"Ollama error {response.status_code}: {response.text}")

        data = response.json()
        raw_text = data.get("response", "")
        
        # Aggressively extract ONLY the JSON payload, cutting out any leftover markdown garbage
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            raw_text = match.group(0)

        return raw_text.strip()
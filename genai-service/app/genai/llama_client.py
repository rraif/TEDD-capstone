import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


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
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 280
                }
            }
        )

        if response.status_code != 200:
            raise RuntimeError(f"Ollama error {response.status_code}: {response.text}")

        data = response.json()
        return data.get("response", "")
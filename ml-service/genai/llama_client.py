import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

async def call_ollama(prompt: str) -> str:
    """
    Calls local Ollama LLaMA model and returns raw text output.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            }
        )

        response.raise_for_status()
        data = response.json()

        return data.get("response", "")
from fastapi import APIRouter, HTTPException
from uuid import uuid4

from .schemas import QuizPlan, TrainingEmail
from .prompts import build_email_prompt, PROMPT_VERSION
from .llama_client import call_ollama
from .guardrails import validate_and_parse_email

router = APIRouter()  # <- THIS is what main.py imports

MODEL_VERSION = "llama3-local"


@router.post("/quiz-batch", response_model=list[TrainingEmail])
async def generate_quiz_batch(plan: QuizPlan):
    results: list[TrainingEmail] = []

    for item in plan.items:
        prompt = build_email_prompt(
            scenario_id=item.scenario_id,
            category=item.category,
            difficulty=item.difficulty,
            language=item.language,
            tone=item.tone,
        )

        raw = await call_ollama(prompt)

        for attempt in range(2):
            try:
                email = validate_and_parse_email(raw)

                if not email.email_id:
                    email.email_id = f"email_{uuid4().hex[:8]}"
                if not email.model_version:
                    email.model_version = MODEL_VERSION
                if not email.prompt_version:
                    email.prompt_version = PROMPT_VERSION

                results.append(email)
                break

            except Exception as e:
                if attempt == 0:
                    raw = await call_ollama(prompt + "\n\nReturn VALID JSON ONLY. No markdown.")
                else:
                    raise HTTPException(status_code=500, detail=f"LLM output validation failed: {str(e)}")

    return results
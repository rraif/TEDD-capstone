from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from uuid import uuid4
from typing import Dict, List, Tuple
import re

from fastapi import APIRouter, HTTPException

from .schemas import (
    QuizPlan,
    TrainingEmail,
    InboxQuizRequest,
)
from .prompts import build_email_prompt, PROMPT_VERSION
from .llama_client import call_ollama
from .guardrails import validate_and_parse_email

MODEL_VERSION = "llama3-local"
router = APIRouter()  # <-- IMPORTANT: no prefix="/gen" here


# ----------------------------
# Helpers (Option B: headers)
# ----------------------------

def _now_rfc2822() -> str:
    return format_datetime(datetime.now(timezone.utc))


def _make_message_id(domain: str = "tedd.training") -> str:
    return f"<{uuid4().hex}@{domain}>"


def _infer_domain(email_addr: str) -> str:
    if not email_addr or "@" not in email_addr:
        return "tedd.training"
    return email_addr.split("@", 1)[1].strip().lower() or "tedd.training"


def _generate_headers(from_email: str, reply_to: str | None = None) -> Dict[str, str]:
    domain = _infer_domain(from_email)
    return {
        "Date": _now_rfc2822(),
        "Message-ID": _make_message_id(domain),
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "From": from_email,
        "Reply-To": from_email,
        "X-TEDD-Training": "true",
    }


# ----------------------------
# Inbox profile (lightweight)
# ----------------------------

_WORD = re.compile(r"[a-zA-Z]{3,}")

def _topic_keywords_from_subjects(subjects: List[str]) -> List[str]:
    # Simple frequency keyword extractor (no heavy NLP needed)
    stop = {
        "your","you","the","and","for","with","from","this","that","have","has","are",
        "was","were","will","can","not","now","please","request","requested","update",
        "invoice","payment","meeting","invite","reset","password","account","security"
    }
    freq: Dict[str, int] = {}
    for s in subjects:
        for w in _WORD.findall(s.lower()):
            if w in stop:
                continue
            freq[w] = freq.get(w, 0) + 1
    # top 8 keywords
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8]]


def _common_sender_domains(from_emails: List[str]) -> List[str]:
    domains: Dict[str, int] = {}
    for e in from_emails:
        d = _infer_domain(e)
        domains[d] = domains.get(d, 0) + 1
    return [d for d, _ in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]]


def _build_inbox_prompt(messages: List[dict], category: str, difficulty: int, language: str, tone: str) -> str:
    subjects = [m.get("subject", "") for m in messages if isinstance(m, dict)]
    froms = [m.get("from_email", "") for m in messages if isinstance(m, dict)]

    topics = _topic_keywords_from_subjects(subjects)
    domains = _common_sender_domains(froms)

    # Keep this prompt strict: JSON only, and we will add headers server-side (Option B)
    return f"""
You are generating ONE training email for a phishing-awareness quiz.

Goal:
- Make the email feel like it belongs in THIS user's inbox style.
- Use the user's common themes + common sender domain patterns (below).
- Output VALID JSON ONLY (no markdown, no extra text).

User inbox hints:
- Common topics/keywords: {topics}
- Common sender domains: {domains}
- Example recent subjects: {subjects[:6]}

Email constraints:
- category: {category}  (phishing or benign)
- difficulty: {difficulty}  (1-5)
- language: {language}  (EN or BM)
- tone: {tone}  (formal or casual)

Difficulty guide:
1 = very obvious phishing
3 = moderately convincing phishing
5 = highly realistic phishing email

IMPORTANT:
- DO NOT include "headers" in the JSON. The server will inject headers.
- Links (if any) MUST be a JSON list of objects: [{{"display_text": "...", "url": "https://tedd.training/..."}}]
- Any url MUST be under https://tedd.training/...

Return JSON with exactly these keys:
{{
  "email_id": "",
  "scenario_id": "",
  "category": "{category}",
  "difficulty": {difficulty},
  "subject": "",
  "from_name": "",
  "from_email": "",
  "reply_to": "",
  "body_text": "",
  "links": [],
  "attachments": [],
  "intended_red_flags": [],
  "ground_truth": "{category}",
  "model_version": "",
  "prompt_version": ""
}}

JSON ONLY.
""".strip()


# ----------------------------
# Endpoints
# ----------------------------

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

        # Retry once if invalid
        for attempt in range(2):
            try:
                email = validate_and_parse_email(raw)

                # Fill required metadata if missing
                email.email_id = email.email_id or f"email_{uuid4().hex[:8]}"
                email.model_version = email.model_version or MODEL_VERSION
                email.prompt_version = email.prompt_version or PROMPT_VERSION

                # Option B headers (server-side)
                if not getattr(email, "headers", None):
                    email.headers = _generate_headers(email.from_email, email.reply_to)

                results.append(email)
                break

            except Exception:
                if attempt == 0:
                    raw = await call_ollama(prompt + "\n\nReturn VALID JSON ONLY.")
                else:
                    raise HTTPException(status_code=500, detail="LLM output validation failed.")

    return results


@router.post("/quiz-from-inbox", response_model=list[TrainingEmail])
async def generate_quiz_from_inbox(req: InboxQuizRequest):
    """
    Node server should call this after it fetches user's inbox message metadata.
    We generate emails that match the user's inbox "feel".
    """
    results: list[TrainingEmail] = []

    # counts
    phishing_n = req.quiz.phishing_count
    benign_n = req.quiz.benign_count

    # overrides (if provided)
    language = req.quiz.language or "EN"
    tone = req.quiz.tone or "formal"

    # basic default difficulty distribution
    def difficulty_for(i: int, total: int) -> int:
        if total <= 1:
            return 2
        # spread 2..4
        return 2 + (i * 2 // max(1, total - 1))

    # build a generation plan: first phishing then benign
    plan: List[Tuple[str, int]] = []
    for i in range(phishing_n):
        plan.append(("phishing", difficulty_for(i, phishing_n)))
    for i in range(benign_n):
        plan.append(("benign", difficulty_for(i, benign_n)))

    for idx, (category, diff) in enumerate(plan, start=1):
        prompt = _build_inbox_prompt(
            messages=[m.model_dump() for m in req.messages],
            category=category,
            difficulty=diff,
            language=language,
            tone=tone,
        )

        raw = await call_ollama(prompt)

        for attempt in range(2):
            try:
                email = validate_and_parse_email(raw)

                # fill metadata
                email.email_id = email.email_id or f"email_{uuid4().hex[:8]}"
                email.scenario_id = email.scenario_id or f"inbox_{category}_{idx:02d}"
                email.model_version = email.model_version or MODEL_VERSION
                email.prompt_version = email.prompt_version or PROMPT_VERSION

                # Option B headers (server-side)
                email.headers = _generate_headers(email.from_email, email.reply_to)

                results.append(email)
                break

            except Exception:
                if attempt == 0:
                    raw = await call_ollama(prompt + "\n\nReturn VALID JSON ONLY.")
                else:
                    raise HTTPException(status_code=500, detail="LLM output validation failed.")

    return results
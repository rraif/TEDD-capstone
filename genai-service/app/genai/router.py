from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
from uuid import uuid4
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import re
import random
import os

load_dotenv("../.env")

from fastapi import APIRouter, HTTPException

from .schemas import (
    QuizPlan,
    TrainingEmail,
    InboxQuizRequest,
)
from .prompts import build_email_prompt, PROMPT_VERSION
from .llama_client import call_ollama
from .guardrails import validate_and_parse_email

MODEL_VERSION = os.environ.get("OLLAMA_MODEL")
router = APIRouter()

# ----------------------------
# Helpers
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
    if not from_email:
        from_email = "system@tedd.training"
        
    domain = _infer_domain(from_email)
    return {
        "Date": _now_rfc2822(),
        "Message-ID": _make_message_id(domain),
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "From": from_email,
        "Reply-To": reply_to or from_email,
        "X-TEDD-Training": "true",
    }

# ----------------------------
# Inbox profile
# ----------------------------

_WORD = re.compile(r"[a-zA-Z]{3,}")

def _topic_keywords_from_subjects(subjects: List[str]) -> List[str]:
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
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8]]

def _common_sender_domains(from_emails: List[str]) -> List[str]:
    domains: Dict[str, int] = {}
    for e in from_emails:
        d = _infer_domain(e)
        domains[d] = domains.get(d, 0) + 1
    return [d for d, _ in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]]

def _build_inbox_prompt(messages: List[dict], category: str, difficulty: int, language: str, tone: str, sub_type: str = "none") -> str:
    subjects = [m.get("subject", "") for m in messages if isinstance(m, dict)]
    froms = [m.get("from_email", "") for m in messages if isinstance(m, dict)]

    topics = _topic_keywords_from_subjects(subjects)
    domains = _common_sender_domains(froms)

    if category == "benign":
        goal_instruction = "Write a realistic, completely safe, boring office email. NO urgency, NO threats."
        diff_guide = "Focus entirely on making it a trustworthy, standard communication."
        link_rule = "Because this is a safe email, the 'links' array MUST be empty: []. NO URLs in the body text."
        sender_rule = "The sender domain MUST perfectly match the company or service being represented. Leave 'reply_to' empty."
    else:
        if sub_type == "bec":
            goal_instruction = "Write a Business Email Compromise (BEC) spear-phishing email. Impersonate an executive or vendor asking for an urgent wire transfer. DO NOT use the sender's name for the recipient."
            diff_guide = "Make it a highly realistic, text-only social engineering attack based purely on trust and urgency."
            link_rule = "Because this is a BEC attack, there are NO LINKS. The 'links' array MUST be empty: []."
            sender_rule = "You MUST use a legitimate-looking 'from_email', but you MUST provide a mismatched, sketchy 'reply_to' address."
        else:
            goal_instruction = "Write a deceptive credential-harvesting phishing email. Pivot the user's context into a fake security alert or account suspension. DO NOT write a marketing newsletter."
            diff_guide = "Difficulty 5 = highly realistic spear-phishing with relevant context."
            link_rule = "You MUST include ONE deceptive link in the 'links' array. The URL MUST start with https://tedd.training/."
            sender_rule = "Use a slightly mismatched 'from_email' domain. Leave 'reply_to' empty."

    return f"""
You are generating ONE training email for a phishing-awareness quiz.

Goal:
- {goal_instruction}
- Make the email heavily localized and realistic using the user's inbox context below.
- Output VALID JSON ONLY (no markdown).

User inbox context to impersonate:
- Recent topics/keywords: {topics}
- Common sender domains: {domains}

Email constraints:
- category: {category}
- language: {language}
- tone: {tone}

{diff_guide}

IMPORTANT RULES:
- DO NOT include "headers" in the JSON.
- DO NOT add disclaimers, training footers, or "(This is a training simulation email.)" to the body_text.
- {link_rule}
- {sender_rule}
- "intended_red_flags" MUST be an empty array: []
- for 'from_email', output ONLY the raw email address (e.g., john@company.com), NO brackets.
- Use \n\n to separate paragraphs and sign-offs in the body_text.

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
            scenario_id=item.scenario_id, category=item.category,
            difficulty=item.difficulty, language=item.language, tone=item.tone,
        )
        raw = await call_ollama(prompt)
        try:
            email = validate_and_parse_email(raw)
            email.email_id = email.email_id or f"email_{uuid4().hex[:8]}"
            results.append(email)
        except Exception as e:
            print(f"Batch generation failed: {e}")
    return results

@router.post("/quiz-from-inbox", response_model=list[TrainingEmail])
async def generate_quiz_from_inbox(req: InboxQuizRequest):
    results: list[TrainingEmail] = []

    phishing_n = req.quiz.phishing_count
    benign_n = req.quiz.benign_count
    language = req.quiz.language or "EN"
    tone = req.quiz.tone or "formal"

    plan: List[Tuple[str, int, str]] = []
    
    for i in range(phishing_n):
        attack_type = random.choice(["link", "bec"])
        plan.append(("phishing", 5, attack_type))
        
    for i in range(benign_n):
        plan.append(("benign", 1, "none"))

    for idx, (category, diff, sub_type) in enumerate(plan, start=1):
        prompt = _build_inbox_prompt(
            messages=[m.model_dump() for m in req.messages],
            category=category, difficulty=diff, language=language,
            tone=tone, sub_type=sub_type
        )

        raw = await call_ollama(prompt)

        for attempt in range(2):
            try:
                email = validate_and_parse_email(raw)

                # 🚀 THE FIX: Deterministic Grading Override
                if category == "benign":
                    email.intended_red_flags = []
                elif sub_type == "bec":
                    email.intended_red_flags = ["mismatched_sender", "financial_request", "urgency"]
                else:
                    email.intended_red_flags = ["suspicious_link", "urgency"]

                email.email_id = email.email_id or f"email_{uuid4().hex[:8]}"
                email.scenario_id = email.scenario_id or f"inbox_{category}_{idx:02d}"
                email.model_version = email.model_version or MODEL_VERSION
                email.prompt_version = email.prompt_version or PROMPT_VERSION

                safe_from = email.from_email if getattr(email, 'from_email', None) else "system@tedd.training"
                email.headers = _generate_headers(safe_from, getattr(email, 'reply_to', safe_from))

                results.append(email)
                break

            except Exception as e:
                print(f"\n[⚠️ GENAI ERROR] Validation failed on attempt {attempt}: {e}\n")
                if attempt == 0:
                    raw = await call_ollama(prompt + "\n\nReturn VALID JSON ONLY. NO MARKDOWN. NO EXTRA TEXT.")
                else:
                    raise HTTPException(status_code=500, detail="Generation failed.")

    return results
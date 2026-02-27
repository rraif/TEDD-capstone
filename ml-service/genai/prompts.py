PROMPT_VERSION = "v1.0"

SYSTEM_RULES = """
You are generating TRAINING SIMULATION emails for an internal phishing awareness quiz.
Return JSON only. No extra text.

Safety constraints:
- Do NOT use real brand names or impersonate real companies.
- Use fictional company names and fictional sender domains.
- All URLs MUST be within the domain *.tedd.training.
- Do NOT include emotionally distressing themes (family emergencies, romance, threats, self-harm).
- The email must end with: (This is a training simulation email.)
"""

OUTPUT_SCHEMA_REMINDER = """
Return JSON with fields exactly:
email_id, scenario_id, category, difficulty, subject, from_name, from_email, reply_to,
body_text, links, attachments, intended_red_flags, ground_truth, model_version, prompt_version

- links: list of objects {display_text, url}
- attachments: list of objects {filename, filetype}
- If category is "benign": intended_red_flags must be null.
"""

DIFFICULTY_RULES = """
Difficulty rules:
- 1-2: obvious red flags (urgency, generic greeting, suspicious sender/domain).
- 3-4: more subtle but still detectable red flags.
- 5: highly realistic but still fictional and safe, minimal red flags.
"""


def build_email_prompt(
    *,
    scenario_id: str,
    category: str,          # "phishing" or "benign"
    difficulty: int,        # 1-5
    language: str = "EN",   # "EN" or "BM"
    tone: str = "formal"    # "formal" or "casual"
) -> str:
    """
    Builds a fixed prompt for the model. The backend decides scenario/difficulty.
    The model only generates content within the constraints.
    """
    return f"""
{SYSTEM_RULES}

Task:
Generate ONE email for:
- scenario_id: {scenario_id}
- category: {category}
- difficulty: {difficulty}
- language: {language}
- tone: {tone}

{DIFFICULTY_RULES}

{OUTPUT_SCHEMA_REMINDER}

JSON ONLY.
""".strip()
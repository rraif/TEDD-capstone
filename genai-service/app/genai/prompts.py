PROMPT_VERSION = "v1.2"

# ------------------------------------
# Standard quiz prompt
# ------------------------------------

def build_email_prompt(item, target_name=""):

    scenario = item.get("scenario_id", "General IT Support")
    category = item.get("category", "phishing")
    difficulty = item.get("difficulty", 5)
    language = item.get("language", "EN")
    tone = item.get("tone", "formal")

    name_instruction = f"Address the email to '{target_name}'." if target_name else "Address the email to a realistic fake name (e.g., 'Sarah', 'Alex') or use a generic professional greeting."

    return f"""
You are generating a training email for a phishing awareness quiz.

Scenario: {scenario}
Category: {category}
Difficulty: {difficulty}/10
Language: {language}
Tone: {tone}

CRITICAL RULES:
1. NO PLACEHOLDERS: NEVER use brackets like [User], [Name], [Insert Link], or [Company].
2. RECIPIENT: {name_instruction}
3. URLS: Invent realistic deceptive URLs (e.g., 'https://secure-billing-update.com/login').
4. SENDER: Invent a realistic sender email that matches the scenario.

Return ONLY valid JSON matching this schema:

{{
  "email_id": "",
  "scenario_id": "{scenario}",
  "category": "{category}",
  "difficulty": {difficulty},
  "subject": "",
  "from_name": "",
  "from_email": "",
  "reply_to": "",
  "headers": {{}},
  "body_text": "",
  "links": [
    {{
      "display_text": "",
      "url": ""
    }}
  ],
  "attachments": [],
  "intended_red_flags": [],
  "ground_truth": "{category}",
  "model_version": "llama3",
  "prompt_version": "{PROMPT_VERSION}"
}}
"""

# ------------------------------------
# Inbox-based quiz prompt
# ------------------------------------

def build_inbox_email_prompt(item, profile, target_name=""):

    scenario = getattr(item, 'scenario_id', "General Phishing")
    category = getattr(item, 'category', "phishing")
    difficulty = getattr(item, 'difficulty', 5)

    topics = ", ".join(profile.get("top_topics", [])) if profile.get("top_topics") else "General Corporate Communications"
    domains = ", ".join(profile.get("common_sender_domains", [])) if profile.get("common_sender_domains") else "standard external vendors"

    name_instruction = f"Address the email to '{target_name}'." if target_name else "Address the email to a realistic fake name or use a generic professional greeting."

    return f"""
You are generating a highly realistic, targeted phishing awareness training email.

User Inbox Profile (MIMIC THESE PATTERNS):
Common topics: {topics}
Common sender domains: {domains}

Scenario: {scenario}
Category: {category} (If 'benign', make it a completely safe, normal email. If 'phishing' or 'bec', make it deceptive).
Difficulty: {difficulty}/10

CRITICAL RULES:
1. NO PLACEHOLDERS: NEVER use brackets like [User], [Name], [Insert Link], or [Company].
2. RECIPIENT: {name_instruction}
3. URLS: DO NOT use 'tedd.training'. Invent realistic deceptive URLs based on the sender domain (e.g., 'https://billing-portal-auth.com').
4. CONTEXT: The email MUST heavily relate to the 'Common topics' and spoof the 'Common sender domains' listed above.

Return ONLY valid JSON in this structure:

{{
  "email_id": "",
  "scenario_id": "{scenario}",
  "category": "{category}",
  "difficulty": {difficulty},
  "subject": "",
  "from_name": "",
  "from_email": "",
  "reply_to": "",
  "headers": {{}},
  "body_text": "",
  "links": [
    {{
      "display_text": "",
      "url": ""
    }}
  ],
  "attachments": [],
  "intended_red_flags": [],
  "ground_truth": "{category}",
  "model_version": "llama3",
  "prompt_version": "{PROMPT_VERSION}"
}}
"""
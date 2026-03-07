PROMPT_VERSION = "v1.1"


# ------------------------------------
# Standard quiz prompt
# ------------------------------------

def build_email_prompt(item):

    scenario = item["scenario_id"]
    category = item["category"]
    difficulty = item["difficulty"]
    language = item.get("language", "EN")
    tone = item.get("tone", "formal")

    return f"""
You are generating a training email for a phishing awareness quiz.

Scenario: {scenario}
Category: {category}
Difficulty: {difficulty}
Language: {language}
Tone: {tone}

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
      "url": "https://tedd.training/example"
    }}
  ],
  "attachments": [],
  "intended_red_flags": [],
  "ground_truth": "{category}",
  "model_version": "llama3-local",
  "prompt_version": "{PROMPT_VERSION}"
}}

Rules:
- Return JSON ONLY
- No explanations
- Links must use https://tedd.training
- Email must end with: (This is a training simulation email.)
"""


# ------------------------------------
# Inbox-based quiz prompt
# ------------------------------------

def build_inbox_email_prompt(item, profile):

    scenario = item.scenario_id
    category = item.category
    difficulty = item.difficulty

    topics = ", ".join(profile.get("top_topics", []))
    domains = ", ".join(profile.get("common_sender_domains", []))

    return f"""
You are generating a phishing awareness training email.

The email must look similar to emails the user normally receives.

User Inbox Profile:
Common topics: {topics}
Common sender domains: {domains}

Scenario: {scenario}
Category: {category}
Difficulty: {difficulty}

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
      "url": "https://tedd.training/example"
    }}
  ],
  "attachments": [],
  "intended_red_flags": [],
  "ground_truth": "{category}",
  "model_version": "llama3-local",
  "prompt_version": "{PROMPT_VERSION}"
}}

Important:
- Make the email resemble real inbox emails
- Use topics similar to: {topics}
- Sender domains may resemble: {domains}
- Links must still use https://tedd.training
- Return JSON ONLY
- Email must end with: (This is a training simulation email.)
"""
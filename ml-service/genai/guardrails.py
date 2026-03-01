import json
import re
from .schemas import TrainingEmail

_ALLOWED_URL = re.compile(
    r"^https://([a-zA-Z0-9\-\._]+\.)?tedd\.training(/[^\s\"]*)?$"
)

TRAINING_FOOTER = "(This is a training simulation email.)"


def _extract_json_block(text: str) -> dict:
    """
    Extracts the first valid JSON object from model output.
    Handles cases where the model adds extra text.
    """
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model did not return valid JSON.")
        return json.loads(text[start:end + 1])


def _enforce_training_footer(body_text: str) -> str:
    body_text = body_text.strip()
    if not body_text.endswith(TRAINING_FOOTER):
        body_text = f"{body_text}\n\n{TRAINING_FOOTER}"
    return body_text


def validate_and_parse_email(raw_text: str) -> TrainingEmail:
    """
    1) Extract JSON safely
    2) Enforce URL allowlist
    3) Enforce training footer
    4) Validate schema
    """

    obj = _extract_json_block(raw_text)

        # ---- Normalize common LLM mistakes ----
    # email_id must be string
    if "email_id" in obj and obj["email_id"] is not None and not isinstance(obj["email_id"], str):
        obj["email_id"] = str(obj["email_id"])

    # model_version / prompt_version must be strings
    if "model_version" in obj and obj["model_version"] is not None and not isinstance(obj["model_version"], str):
        obj["model_version"] = str(obj["model_version"])

    if "prompt_version" in obj and obj["prompt_version"] is not None and not isinstance(obj["prompt_version"], str):
        obj["prompt_version"] = str(obj["prompt_version"])

    # ground_truth must be "phishing" or "benign"
    gt = obj.get("ground_truth")
    if isinstance(gt, int):
        obj["ground_truth"] = "phishing" if gt == 1 else "benign"
    elif isinstance(gt, str):
        low = gt.strip().lower()
        if low in ["phish", "phishing"]:
            obj["ground_truth"] = "phishing"
        elif low in ["benign", "legit", "legitimate", "safe"]:
            obj["ground_truth"] = "benign"

    # Enforce footer
    if "body_text" in obj and isinstance(obj["body_text"], str):
        obj["body_text"] = _enforce_training_footer(obj["body_text"])

    # Validate links
    links = obj.get("links", [])
    if not isinstance(links, list):
        raise ValueError("links must be a list")

    for link in links:
        url = link.get("url", "")
        if url and not _ALLOWED_URL.match(url):
            raise ValueError(f"Disallowed URL: {url}")

    # Benign emails should not have red flags
    if obj.get("category") == "benign":
        obj["intended_red_flags"] = None

    # Ensure ground_truth exists
    if "ground_truth" not in obj:
        obj["ground_truth"] = obj.get("category")

    return TrainingEmail(**obj)
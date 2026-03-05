import json
import re
from typing import Any, Dict, List
from .schemas import TrainingEmail

# Only allow training links (safety + consistency)
_ALLOWED_URL = re.compile(
    r"^https://([a-zA-Z0-9\-\._]+\.)?tedd\.training(/[^\s\"]*)?$"
)

TRAINING_FOOTER = "(This is a training simulation email.)"


def _extract_json_block(text: str) -> Dict[str, Any]:
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
        return json.loads(text[start : end + 1])


def _enforce_training_footer(body_text: str) -> str:
    body_text = (body_text or "").strip()
    if not body_text.endswith(TRAINING_FOOTER):
        body_text = f"{body_text}\n\n{TRAINING_FOOTER}".strip()
    return body_text


def _normalize_links(obj: Dict[str, Any]) -> None:
    """
    Make sure obj["links"] becomes a list[dict] with {display_text, url}.
    Common LLM mistakes:
      - links is a dict
      - links is a string
      - links missing
      - items missing keys
    """
    links = obj.get("links", [])
    if links is None:
        obj["links"] = []
        return

    # If model returns single dict, wrap it.
    if isinstance(links, dict):
        links = [links]

    # If model returns string, treat as single URL
    if isinstance(links, str):
        links = [{"display_text": "Open Link", "url": links.strip()}]

    if not isinstance(links, list):
        raise ValueError("links must be a list")

    cleaned: List[Dict[str, str]] = []
    for item in links:
        if not isinstance(item, dict):
            continue
        display_text = str(item.get("display_text") or item.get("text") or "Open Link")
        url = str(item.get("url") or "").strip()

        # Keep empty URLs out
        if not url:
            continue

        cleaned.append({"display_text": display_text, "url": url})

    obj["links"] = cleaned


def _enforce_url_allowlist(obj: Dict[str, Any]) -> None:
    for link in obj.get("links", []):
        url = (link.get("url") or "").strip()
        if url and not _ALLOWED_URL.match(url):
            raise ValueError(f"Disallowed URL: {url}")


def _normalize_types(obj: Dict[str, Any]) -> None:
    # email_id must be string if present
    if "email_id" in obj and obj["email_id"] is not None and not isinstance(obj["email_id"], str):
        obj["email_id"] = str(obj["email_id"])

    # model_version / prompt_version must be strings if present
    if "model_version" in obj and obj["model_version"] is not None and not isinstance(obj["model_version"], str):
        obj["model_version"] = str(obj["model_version"])

    if "prompt_version" in obj and obj["prompt_version"] is not None and not isinstance(obj["prompt_version"], str):
        obj["prompt_version"] = str(obj["prompt_version"])

    # difficulty if returned as string -> int
    if "difficulty" in obj and isinstance(obj["difficulty"], str) and obj["difficulty"].isdigit():
        obj["difficulty"] = int(obj["difficulty"])

    # Ensure headers exists as dict
    headers = obj.get("headers")
    if headers is None:
        obj["headers"] = {}
    elif not isinstance(headers, dict):
        obj["headers"] = {}


def _enforce_required_fields(obj: Dict[str, Any]) -> None:
    # Never allow empty subject
    if not obj.get("subject"):
        obj["subject"] = "Important Account Notification"

    # Enforce footer in body
    if "body_text" in obj and isinstance(obj["body_text"], str):
        obj["body_text"] = _enforce_training_footer(obj["body_text"])
    else:
        obj["body_text"] = _enforce_training_footer(str(obj.get("body_text") or ""))

    # Benign emails should not have red flags
    if obj.get("category") == "benign":
        obj["intended_red_flags"] = None


def validate_and_parse_email(raw_text: str) -> TrainingEmail:
    """
    1) Extract JSON safely
    2) Normalize common LLM mistakes
    3) Enforce URL allowlist
    4) Enforce training footer + required fields
    5) Force ground_truth = category
    6) Validate schema
    """
    obj = _extract_json_block(raw_text)

    _normalize_types(obj)
    _normalize_links(obj)
    _enforce_url_allowlist(obj)
    _enforce_required_fields(obj)

    # ✅ Always force ground_truth to match category (no exceptions)
    obj["ground_truth"] = obj.get("category")

    return TrainingEmail(**obj)
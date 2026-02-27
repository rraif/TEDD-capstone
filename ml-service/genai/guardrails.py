import json
import re
from .schemas import TrainingEmail

# Only allow safe training links
_ALLOWED_URL = re.compile(r"^https://[a-zA-Z0-9\-\._]+\.tedd\.training(/[^\s\"]*)?$")

TRAINING_FOOTER = "(This is a training simulation email.)"


def _enforce_training_footer(body_text: str) -> str:
    body_text = body_text.strip()
    if not body_text.endswith(TRAINING_FOOTER):
        body_text = f"{body_text}\n\n{TRAINING_FOOTER}"
    return body_text


def validate_and_parse_email(raw_text: str) -> TrainingEmail:
    """
    1) Parse JSON
    2) Enforce URL allowlist
    3) Enforce training footer
    4) Validate schema via Pydantic
    """
    obj = json.loads(raw_text)

    # Enforce footer
    if "body_text" in obj and isinstance(obj["body_text"], str):
        obj["body_text"] = _enforce_training_footer(obj["body_text"])

    # Enforce allowed URLs
    links = obj.get("links", [])
    if not isinstance(links, list):
        raise ValueError("links must be a list")

    for link in links:
        url = link.get("url", "")
        if url and not _ALLOWED_URL.match(url):
            raise ValueError(f"Disallowed URL: {url}")

    # If benign, intended_red_flags should be null/None
    if obj.get("category") == "benign":
        obj["intended_red_flags"] = None

    # ground_truth should match category
    if "ground_truth" not in obj:
        obj["ground_truth"] = obj.get("category")

    return TrainingEmail(**obj)
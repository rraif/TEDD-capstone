from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class QuizItem(BaseModel):
    scenario_id: str
    category: Literal["phishing", "benign"]
    difficulty: int = Field(ge=1, le=5)
    language: Literal["EN", "BM"] = "EN"
    tone: Literal["formal", "casual"] = "formal"


class QuizPlan(BaseModel):
    quiz_id: str
    items: List[QuizItem]


class Link(BaseModel):
    display_text: str
    url: str


class Attachment(BaseModel):
    filename: str
    filetype: str


class TrainingEmail(BaseModel):
    email_id: str
    scenario_id: str
    category: Literal["phishing", "benign"]
    difficulty: int = Field(ge=1, le=5)

    subject: str
    from_name: str
    from_email: str
    reply_to: Optional[str] = None

    body_text: str
    links: List[Link] = []
    attachments: List[Attachment] = []

    # phishing only (benign should be null/None)
    intended_red_flags: Optional[List[str]] = None

    # used for scoring
    ground_truth: Literal["phishing", "benign"]

    # for tracking & reproducibility
    model_version: str
    prompt_version: str
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict


# ---------------------------
# Quiz Input Models
# ---------------------------

class QuizItem(BaseModel):
    scenario_id: str
    category: Literal["phishing", "benign"]
    difficulty: int = Field(ge=1, le=5)
    language: Literal["EN", "BM"] = "EN"
    tone: Literal["formal", "casual"] = "formal"


class QuizPlan(BaseModel):
    quiz_id: str
    items: List[QuizItem]


# ---------------------------
# Email Structure Models
# ---------------------------

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
    difficulty: int

    subject: str
    from_name: str
    from_email: str
    reply_to: Optional[str] = None

    # Headers default to empty dict (prevents missing error)
    headers: Dict[str, str] = Field(default_factory=dict)

    body_text: str
    links: List[Link] = Field(default_factory=list)
    attachments: List[Attachment] = Field(default_factory=list)

    intended_red_flags: Optional[List[str]] = None
    ground_truth: Literal["phishing", "benign"]

    model_version: str
    prompt_version: str


# ---------------------------
# Inbox Profile Models
# ---------------------------

class InboxProfile(BaseModel):
    user_id: str
    top_topics: List[str]
    topic_weights: Dict[str, float]
    language: Literal["EN", "BM"]
    tone: Literal["formal", "casual"]
    common_sender_domains: List[str]


class GmailMessageMeta(BaseModel):
    subject: str = ""
    from_email: str = ""


class InboxQuizSettings(BaseModel):
    quiz_id: str
    phishing_count: int = Field(ge=0, le=50)
    benign_count: int = Field(ge=0, le=50)
    language: Optional[Literal["EN", "BM"]] = None
    tone: Optional[Literal["formal", "casual"]] = None


class InboxQuizRequest(BaseModel):
    user_id: str
    messages: List[GmailMessageMeta]
    quiz: InboxQuizSettings
import random
import re
from collections import Counter
from typing import List

from .schemas import (
    InboxProfile,
    GmailMessageMeta,
    InboxQuizSettings,
    QuizItem
)

# ----------------------------------
# Topic keyword detection
# ----------------------------------

TOPIC_KEYWORDS = {
    "password": ["password", "reset", "login", "verify"],
    "delivery": ["delivery", "shipment", "package", "tracking"],
    "invoice": ["invoice", "payment", "receipt", "billing"],
    "meeting": ["meeting", "calendar", "schedule", "invite"],
    "account": ["account", "security", "alert"],
    "subscription": ["subscription", "renew", "plan"],
}


def _detect_topics(messages: List[GmailMessageMeta]):

    topic_counter = Counter()

    for msg in messages:
        subject = (msg.subject or "").lower()

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(k in subject for k in keywords):
                topic_counter[topic] += 1

    if not topic_counter:
        topic_counter["general"] = 1

    total = sum(topic_counter.values())

    topic_weights = {
        topic: count / total
        for topic, count in topic_counter.items()
    }

    return list(topic_counter.keys()), topic_weights


# ----------------------------------
# Extract sender domains
# ----------------------------------

def _extract_domains(messages: List[GmailMessageMeta]):

    domains = []

    for msg in messages:
        email = (msg.from_email or "").lower()

        if "@" in email:
            domain = email.split("@")[1]
            domains.append(domain)

    return list(set(domains))


# ----------------------------------
# Build quiz items
# ----------------------------------

def _build_quiz_items(
    topics,
    quiz: InboxQuizSettings
):

    items = []

    # phishing emails
    for _ in range(quiz.phishing_count):

        topic = random.choice(topics)

        items.append(
            QuizItem(
                scenario_id=f"{topic}_phish",
                category="phishing",
                difficulty=random.randint(2, 4),
                language=quiz.language or "EN",
                tone=quiz.tone or "formal"
            )
        )

    # benign emails
    for _ in range(quiz.benign_count):

        topic = random.choice(topics)

        items.append(
            QuizItem(
                scenario_id=f"{topic}_benign",
                category="benign",
                difficulty=random.randint(2, 4),
                language=quiz.language or "EN",
                tone=quiz.tone or "formal"
            )
        )

    random.shuffle(items)

    return items


# ----------------------------------
# Main profile builder
# ----------------------------------

def build_inbox_profile(
    user_id: str,
    messages: List[GmailMessageMeta],
    quiz: InboxQuizSettings
):

    topics, topic_weights = _detect_topics(messages)

    domains = _extract_domains(messages)

    items = _build_quiz_items(topics, quiz)

    profile = InboxProfile(
        user_id=user_id,
        top_topics=topics,
        topic_weights=topic_weights,
        language=quiz.language or "EN",
        tone=quiz.tone or "formal",
        common_sender_domains=domains
    )

    # attach generated items (used by router)
    profile.generated_items = items

    return profile
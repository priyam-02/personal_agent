import logging
from dataclasses import dataclass

logger = logging.getLogger("nemoclaw.classifier")


@dataclass
class ClassifiedEmail:
    should_notify: bool
    priority: str  # "high", "normal", "low"
    reason: str


# Domains/patterns that are almost always noise
NOISE_SENDERS = [
    "noreply@",
    "no-reply@",
    "notifications@",
    "mailer-daemon@",
    "donotreply@",
    "newsletter@",
    "marketing@",
    "promo@",
    "deals@",
    "news@",
    "digest@",
    "updates@github.com",
]

# Subject patterns that suggest low-priority automated mail
NOISE_SUBJECTS = [
    "unsubscribe",
    "your weekly",
    "your monthly",
    "your daily",
    "price drop",
    "sale ends",
    "order confirmation",
    "shipping notification",
    "delivery notification",
    "password reset",
    "verify your email",
    "confirm your",
]

# Patterns that suggest high priority
HIGH_PRIORITY_PATTERNS = [
    "urgent",
    "asap",
    "action required",
    "action needed",
    "deadline",
    "overdue",
    "interview",
    "offer letter",
    "contract",
    "invoice due",
    "payment due",
]


def classify_email(
    sender_email: str,
    subject: str,
    category: str,
    labels: list[str],
    skip_categories: list[str],
) -> ClassifiedEmail:
    """Classify an email to decide if the user should be notified."""

    sender_lower = sender_email.lower()
    subject_lower = subject.lower()

    # 1) Skip Gmail categories the user doesn't want
    if category in skip_categories:
        return ClassifiedEmail(
            should_notify=False,
            priority="low",
            reason=f"Skipped category: {category}",
        )

    # 2) Skip known noise senders
    for pattern in NOISE_SENDERS:
        if pattern in sender_lower:
            return ClassifiedEmail(
                should_notify=False,
                priority="low",
                reason=f"Noise sender: {pattern}",
            )

    # 3) Skip noise subjects
    for pattern in NOISE_SUBJECTS:
        if pattern in subject_lower:
            return ClassifiedEmail(
                should_notify=False,
                priority="low",
                reason=f"Noise subject pattern: {pattern}",
            )

    # 4) Check for high priority
    for pattern in HIGH_PRIORITY_PATTERNS:
        if pattern in subject_lower:
            return ClassifiedEmail(
                should_notify=True,
                priority="high",
                reason=f"High-priority keyword: {pattern}",
            )

    # 5) If it's in IMPORTANT label, bump priority
    if "IMPORTANT" in labels:
        return ClassifiedEmail(
            should_notify=True,
            priority="high",
            reason="Marked important by Gmail",
        )

    # 6) Default: notify at normal priority
    return ClassifiedEmail(
        should_notify=True,
        priority="normal",
        reason="Passed all filters",
    )

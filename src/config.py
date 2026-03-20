import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # Gmail
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    gmail_labels: list[str] = field(default_factory=lambda: ["INBOX"])
    skip_categories: list[str] = field(
        default_factory=lambda: ["promotions", "social", "updates", "forums"]
    )

    # Behavior
    max_emails_per_poll: int = 10
    db_path: str = "/sandbox/nemoclaw.db"

    @classmethod
    def from_env(cls) -> "Config":
        labels_raw = os.getenv("GMAIL_LABELS", "INBOX")
        skip_raw = os.getenv("SKIP_CATEGORIES", "promotions,social,updates,forums")

        cfg = cls(
            gmail_client_id=os.getenv("GMAIL_CLIENT_ID", ""),
            gmail_client_secret=os.getenv("GMAIL_CLIENT_SECRET", ""),
            gmail_refresh_token=os.getenv("GMAIL_REFRESH_TOKEN", ""),
            gmail_labels=[l.strip() for l in labels_raw.split(",") if l.strip()],
            skip_categories=[c.strip().lower() for c in skip_raw.split(",") if c.strip()],
            max_emails_per_poll=int(os.getenv("MAX_EMAILS_PER_POLL", "10")),
            db_path=os.getenv("DB_PATH", "/sandbox/nemoclaw.db"),
        )
        cfg.validate()
        return cfg

    def validate(self):
        missing = []
        if not self.gmail_client_id:
            missing.append("GMAIL_CLIENT_ID")
        if not self.gmail_client_secret:
            missing.append("GMAIL_CLIENT_SECRET")
        if not self.gmail_refresh_token:
            missing.append("GMAIL_REFRESH_TOKEN (run setup_gmail.py first)")
        if missing:
            raise EnvironmentError(
                "Missing required env vars:\n  - " + "\n  - ".join(missing)
            )

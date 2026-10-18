from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    """Return UTC as a naive datetime for legacy timezone-naive DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

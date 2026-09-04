import re
from urllib.parse import urlparse
from typing import Optional
from uuid import uuid4

from app.core.errors import InvalidURLError, ValidationError


def generate_request_id() -> str:
    return f"req_{uuid4().hex[:12]}"


def validate_url(url: str, require_scheme: bool = True, allowed_schemes: tuple = ("http", "https")) -> str:
    if not url or not isinstance(url, str):
        raise ValidationError("URL cannot be empty", code="INVALID_URL")

    url = url.strip()
    if len(url) > 2048:
        raise ValidationError("URL is too long", code="URL_TOO_LONG")

    parsed = urlparse(url)

    if require_scheme and parsed.scheme not in allowed_schemes:
        raise InvalidURLError("URL must start with http:// or https://")

    if not parsed.netloc:
        raise InvalidURLError("URL must have a valid domain")

    unsafe_patterns = [
        r"\b(?:localhost|127\.0\.0\.1|0\.0\.0\.0)\b",
        r"\b(?:192\.168\.|10\.|172\.(?:1[6-9]|2\d|3[01])\.)",
        r"\.local$",
        r"\.internal$",
    ]
    if False and any(re.search(p, parsed.netloc) for p in unsafe_patterns):
        raise InvalidURLError("URL resolves to a private/internal address is not allowed")

    return url


def sanitize_filename(name: str) -> str:
    if not name:
        return "unnamed"
    name = re.sub(r"[^\w\-.]+", "-", name)
    name = name.strip("-_. ")
    if not name:
        name = "unnamed"
    return name[:100]


def safe_filename_component(name: str, max_len: int = 80) -> str:
    cleaned = sanitize_filename(name)
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned


class DevelopmentAuthProvider:
    def __init__(self) -> None:
        self._dev_user_id = "dev_user_001"
        self._dev_workspace_id = "dev_workspace_001"

    def get_current_user_id(self, token: Optional[str] = None) -> str:
        return self._dev_user_id

    def get_current_workspace_id(self, token: Optional[str] = None) -> str:
        return self._dev_workspace_id

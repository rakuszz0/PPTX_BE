import json
import os
from typing import Optional, Dict
from pathlib import Path
import secrets
import hashlib

BASE = Path(os.getcwd()) / "data"
BASE.mkdir(parents=True, exist_ok=True)
USERS_FILE = BASE / "auth_users.json"
TOKENS_FILE = BASE / "auth_tokens.json"


def _read(file: Path) -> Optional[dict]:
    try:
        if not file.exists():
            return None
        with file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write(file: Path, data: dict):
    with file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _users() -> Dict[str, dict]:
    v = _read(USERS_FILE)
    return v or {}


def _tokens() -> Dict[str, dict]:
    v = _read(TOKENS_FILE)
    return v or {}


def _save_users(u: Dict[str, dict]):
    _write(USERS_FILE, u)


def _save_tokens(t: Dict[str, dict]):
    _write(TOKENS_FILE, t)


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), n=16384, r=8, p=1, dklen=64)
    return f"{salt}${dk.hex()}"


def _check_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$")
        dk = hashlib.scrypt(password.encode("utf-8"), salt=salt.encode("utf-8"), n=16384, r=8, p=1, dklen=64)
        return dk.hex() == h
    except Exception:
        return False


def create_user(username: str, password: str, display_name: Optional[str] = None, role: str = "editor") -> Optional[dict]:
    users = _users()
    if username in users:
        return None
    uid = f"u_{secrets.token_hex(6)}"
    pw = _hash_password(password)
    obj = {"id": uid, "username": username, "display_name": display_name or username, "role": role, "password_hash": pw}
    users[username] = obj
    _save_users(users)
    return {k: v for k, v in obj.items() if k != "password_hash"}


def validate_credentials(username: str, password: str) -> Optional[dict]:
    users = _users()
    u = users.get(username)
    if not u:
        return None
    ph = u.get("password_hash")
    if not ph:
        return None
    if not _check_password(password, ph):
        return None
    return {k: v for k, v in u.items() if k != "password_hash"}


def create_token_for_user(user: dict) -> str:
    tokens = _tokens()
    token = f"tok_{secrets.token_hex(12)}"
    tokens[token] = user
    _save_tokens(tokens)
    return token


def get_user_for_token(token: str) -> Optional[dict]:
    tokens = _tokens()
    return tokens.get(token)


def invalidate_token(token: str):
    tokens = _tokens()
    if token in tokens:
        del tokens[token]
        _save_tokens(tokens)


def get_or_create_oauth_user(
    provider: str,
    provider_user_id: str,
    email: str,
    display_name: Optional[str] = None,
    role: str = "editor",
) -> dict:
    """Cari user yang sudah terikat provider OAuth, atau buat baru.

    `email` dipakai sebagai username utama (jika belum ada user dengan email
    tersebut). Jika user dengan username=email sudah ada, tambahkan mapping
    provider ke user itu saja.
    """
    users = _users()
    oauth_key = f"{provider}:::{provider_user_id}"

    # 1. Cari user yang sudah memiliki mapping provider ini
    for uname, u in users.items():
        provs = u.get("oauth_providers") or {}
        if provs.get(provider) == provider_user_id:
            return {k: v for k, v in u.items() if k != "password_hash"}

    # 2. Cari user dengan username == email (sudah punya akun email/password)
    username = email.lower().strip()
    existing = users.get(username)
    if existing:
        existing.setdefault("oauth_providers", {})[provider] = provider_user_id
        if not existing.get("display_name") and display_name:
            existing["display_name"] = display_name
        users[username] = existing
        _save_users(users)
        return {k: v for k, v in existing.items() if k != "password_hash"}

    # 3. User benar-benar baru: buat tanpa password (hanya bisa login via OAuth)
    uid = f"u_{secrets.token_hex(6)}"
    obj = {
        "id": uid,
        "username": username,
        "display_name": display_name or email.split("@")[0],
        "role": role,
        "password_hash": None,
        "oauth_providers": {provider: provider_user_id},
    }
    users[username] = obj
    _save_users(users)
    return {k: v for k, v in obj.items() if k != "password_hash"}

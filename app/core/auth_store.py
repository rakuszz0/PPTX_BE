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

import base64
import json
import urllib.parse
import secrets
from typing import Optional
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import RedirectResponse

from app.core.auth_store import (
    create_user, validate_credentials, create_token_for_user,
    get_user_for_token, invalidate_token, get_or_create_oauth_user,
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_cookie(token: str, secure: bool) -> str:
    cookie = f"auth_token={token}; HttpOnly; Path=/; Max-Age={60*60*24*7}; SameSite=Lax"
    if secure:
        cookie += "; Secure"
    return cookie


# ---------------------------------------------------------------------------
# Email / password
# ---------------------------------------------------------------------------
@router.post("/register")
async def register(req: Request, response: Response):
    body = await req.json()
    username = body.get("username")
    password = body.get("password")
    display = body.get("displayName")
    if not username or not password:
        return Response(content='{"error":"username and password required"}', status_code=400, media_type="application/json")
    if len(password) < 6:
        return Response(content='{"error":"password must be at least 6 characters"}', status_code=400, media_type="application/json")
    user = create_user(username, password, display)
    if not user:
        return Response(content='{"error":"user exists"}', status_code=409, media_type="application/json")
    token = create_token_for_user(user)
    response.headers.append("Set-Cookie", _auth_cookie(token, req.url.scheme == "https"))
    return {"user": user}


@router.post("/login")
async def login(req: Request, response: Response):
    body = await req.json()
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return Response(content='{"error":"username and password required"}', status_code=400, media_type="application/json")
    user = validate_credentials(username, password)
    if not user:
        return Response(content='{"error":"invalid credentials"}', status_code=401, media_type="application/json")
    token = create_token_for_user(user)
    response.headers.append("Set-Cookie", _auth_cookie(token, req.url.scheme == "https"))
    return {"user": user}


@router.post("/logout")
async def logout(request: Request, response: Response):
    auth = request.headers.get("Authorization") or ""
    token = auth.replace("Bearer ", "") if auth else request.cookies.get("auth_token")
    if token:
        invalidate_token(token)
    cookie = f"auth_token=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax"
    if request.url.scheme == "https":
        cookie += "; Secure"
    response.headers.append("Set-Cookie", cookie)
    return {"ok": True}


@router.get("/me")
async def me(request: Request):
    auth = request.headers.get("Authorization") or ""
    token = auth.replace("Bearer ", "") if auth else request.cookies.get("auth_token")
    user = None
    if token:
        user = get_user_for_token(token)
    if not user:
        return Response(content='{"error":"not authenticated"}', status_code=401, media_type="application/json")
    return {"user": user}


# ---------------------------------------------------------------------------
# OAuth 2.0: Google, GitHub, Facebook, Yahoo
# ---------------------------------------------------------------------------
# Provider metadata:
#   authorize_url   : tempat user disodori form login provider
#   token_url       : tuker authorization_code -> access_token
#   userinfo_url    : ambil email + nama dari access_token
#   default_scope   : scope minimal (email + profile)
PROVIDERS: dict = {
    "google": {
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "default_scope": "openid email profile",
        "client_id_key": "GOOGLE_CLIENT_ID",
        "client_secret_key": "GOOGLE_CLIENT_SECRET",
    },
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "user_email_url": "https://api.github.com/user/emails",
        "default_scope": "user:email read:user",
        "client_id_key": "GITHUB_CLIENT_ID",
        "client_secret_key": "GITHUB_CLIENT_SECRET",
    },
    "facebook": {
        "authorize_url": "https://www.facebook.com/v20.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v20.0/oauth/access_token",
        "userinfo_url": "https://graph.facebook.com/v20.0/me?fields=id,name,email",
        "default_scope": "email public_profile",
        "client_id_key": "FACEBOOK_CLIENT_ID",
        "client_secret_key": "FACEBOOK_CLIENT_SECRET",
    },
    "yahoo": {
        "authorize_url": "https://api.login.yahoo.com/oauth2/request_auth",
        "token_url": "https://api.login.yahoo.com/oauth2/get_token",
        "userinfo_url": "https://api.login.yahoo.com/openid/v1/userinfo",
        "default_scope": "openid email profile",
        "client_id_key": "YAHOO_CLIENT_ID",
        "client_secret_key": "YAHOO_CLIENT_SECRET",
    },
}


def _provider_config(provider: str) -> Optional[dict]:
    meta = PROVIDERS.get(provider)
    if not meta:
        return None
    settings = get_settings()
    client_id = getattr(settings, meta["client_id_key"], "") or ""
    client_secret = getattr(settings, meta["client_secret_key"], "") or ""
    if not client_id or not client_secret:
        return None
    return {**meta, "client_id": client_id, "client_secret": client_secret}


def _base_url(request: Request) -> str:
    settings = get_settings()
    return settings.API_BASE_URL.rstrip("/") or f"{request.url.scheme}://{request.headers.get('host', '')}"


@router.get("/providers")
async def list_providers():
    """Kembalikan daftar provider OAuth yang sudah dikonfigurasi (client_id terisi).

    Dipakai frontend untuk menentukan tombol sosial mana yang aktif vs disabled.
    """
    settings = get_settings()
    result = {}
    for name, meta in PROVIDERS.items():
        cid = getattr(settings, meta["client_id_key"], "") or ""
        result[name] = {
            "enabled": bool(cid),
            "client_id": cid[:8] + "…" if len(cid) > 12 else cid,
        }
    return {"providers": result}


@router.get("/oauth/redirect/{provider}")
async def oauth_redirect(provider: str, request: Request):
    """Redirect ke halaman login provider OAuth (Google/GitHub/Facebook/Yahoo).

    Simpan state (CSRF) di cookie `oauth_state` lalu redirect.
    """
    cfg = _provider_config(provider)
    if not cfg:
        settings = get_settings()
        params = urllib.parse.urlencode({
            "oauth_error": f"Provider {provider} belum dikonfigurasi di server (client ID/secret kosong)",
        })
        return RedirectResponse(url=f"{settings.OAUTH_REDIRECT_FRONTEND}?{params}")

    state = secrets.token_urlsafe(24)
    settings = get_settings()
    callback = f"{_base_url(request)}/api/v1/auth/oauth/callback/{provider}"

    query = {
        "client_id": cfg["client_id"],
        "redirect_uri": callback,
        "response_type": "code",
        "scope": cfg["default_scope"],
        "state": state,
    }
    # Provider-specific tweaks
    if provider == "google":
        query["access_type"] = "offline"
        query["prompt"] = "select_account"
    elif provider == "facebook":
        query["auth_type"] = "rerequest"

    authorize = cfg["authorize_url"] + "?" + urllib.parse.urlencode(query)
    resp = RedirectResponse(url=authorize)
    secure = request.url.scheme == "https"
    cookie = f"oauth_state={provider}:{state}; Path=/; Max-Age=600; SameSite=Lax; HttpOnly"
    if secure:
        cookie += "; Secure"
    resp.headers.append("Set-Cookie", cookie)
    return resp


@router.get("/oauth/callback/{provider}")
async def oauth_callback(provider: str, request: Request, response: Response):
    """Handle callback dari provider OAuth: tuker code -> token -> userinfo -> login lokal."""
    import httpx

    settings = get_settings()
    frontend_base = settings.OAUTH_REDIRECT_FRONTEND.rstrip("/")

    def _error_redirect(message: str) -> RedirectResponse:
        params = urllib.parse.urlencode({"oauth_error": message})
        return RedirectResponse(url=f"{frontend_base}?{params}")

    cfg = _provider_config(provider)
    if not cfg:
        return _error_redirect(f"Provider {provider} belum dikonfigurasi")

    # Validasi state CSRF
    expected_state_cookie = request.cookies.get("oauth_state") or ""
    if expected_state_cookie.startswith(provider + ":"):
        expected_state = expected_state_cookie.split(":", 1)[1]
    else:
        expected_state = ""
    qp = request.query_params
    received_state = qp.get("state") or ""
    if not expected_state or expected_state != received_state:
        return _error_redirect("State OAuth tidak valid. Coba login ulang.")

    error = qp.get("error")
    if error:
        desc = qp.get("error_description") or error
        return _error_redirect(f"Login {provider} ditolak: {desc}")

    code = qp.get("code")
    if not code:
        return _error_redirect(f"Provider {provider} tidak mengembalikan authorization code")

    callback = f"{_base_url(request)}/api/v1/auth/oauth/callback/{provider}"
    secure = request.url.scheme == "https"

    # 1. Tuker code -> access_token
    token_body = {
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": code,
        "redirect_uri": callback,
        "grant_type": "authorization_code",
    }
    # Yahoo butuh Basic auth header + grant_type di body (pakai grant_type di body saja sudah cukup)
    headers = {"Accept": "application/json"}
    if provider == "yahoo":
        basic = base64.b64encode(f"{cfg['client_id']}:{cfg['client_secret']}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(cfg["token_url"], data=token_body, headers=headers)
            if r.status_code >= 400:
                logger.warning("oauth token exchange failed %s: %s", provider, r.text)
                return _error_redirect(f"Gagal mendapatkan token dari {provider}")
            token_data = r.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return _error_redirect(f"Token access dari {provider} tidak ditemukan")

            # 2. Ambil user info
            auth_header = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            email = None
            name = None
            uid = None

            if provider == "github":
                # Basic profile
                r_user = await client.get(cfg["userinfo_url"], headers=auth_header)
                if r_user.status_code >= 400:
                    return _error_redirect(f"Gagal mengambil data profil dari {provider}")
                info = r_user.json()
                uid = str(info.get("id") or "")
                name = info.get("name") or info.get("login")
                email = info.get("email")
                # Github private email -> perlu cek /user/emails
                if not email:
                    r_em = await client.get(cfg.get("user_email_url", ""), headers=auth_header)
                    if r_em.status_code < 300:
                        emails = r_em.json() or []
                        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                        if primary:
                            email = primary.get("email")
            else:
                r_user = await client.get(cfg["userinfo_url"], headers=auth_header)
                if r_user.status_code >= 400:
                    return _error_redirect(f"Gagal mengambil data profil dari {provider}")
                info = r_user.json()
                # Google / Yahoo OpenID-style
                uid = str(info.get("sub") or info.get("id") or "")
                # Facebook
                if provider == "facebook":
                    uid = str(info.get("id") or uid)
                email = info.get("email")
                name = info.get("name") or info.get("given_name")

            if not email:
                return _error_redirect(
                    f"Provider {provider} tidak mengirimkan email. Pastikan Anda mengizinkan akses email."
                )
            if not uid:
                return _error_redirect(f"Provider {provider} tidak mengembalikan user ID")
    except Exception as exc:
        logger.exception("oauth flow failed: %s", exc)
        return _error_redirect(f"Terjadi kesalahan koneksi ke {provider}: {exc}")

    # 3. Buat / cari user lokal + issue session cookie
    user = get_or_create_oauth_user(provider, uid, email, name)
    token = create_token_for_user(user)
    response.headers.append("Set-Cookie", _auth_cookie(token, secure))
    # Hapus state cookie
    response.headers.append(
        "Set-Cookie",
        f"oauth_state=; Path=/; Max-Age=0; SameSite=Lax; HttpOnly" + ("; Secure" if secure else ""),
    )

    # Sukses -> redirect ke frontend profile (tanpa query)
    return RedirectResponse(url=f"{frontend_base}?oauth=success")

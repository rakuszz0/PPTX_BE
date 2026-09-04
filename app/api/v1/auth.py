from fastapi import APIRouter, Request, Response, status
from typing import Optional
from app.core.auth_store import create_user, validate_credentials, create_token_for_user, get_user_for_token, invalidate_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(req: Request, response: Response):
    body = await req.json()
    username = body.get("username")
    password = body.get("password")
    display = body.get("displayName")
    if not username or not password:
        return Response(content='{"error":"username and password required"}', status_code=400, media_type="application/json")
    user = create_user(username, password, display)
    if not user:
        return Response(content='{"error":"user exists"}', status_code=409, media_type="application/json")
    token = create_token_for_user(user)
    cookie = f"auth_token={token}; HttpOnly; Path=/; Max-Age={60*60*24*7}; SameSite=Lax"
    if req.url.scheme == "https":
        cookie += "; Secure"
    response.headers.append("Set-Cookie", cookie)
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
    cookie = f"auth_token={token}; HttpOnly; Path=/; Max-Age={60*60*24*7}; SameSite=Lax"
    if req.url.scheme == "https":
        cookie += "; Secure"
    response.headers.append("Set-Cookie", cookie)
    return {"user": user}


@router.post("/logout")
async def logout(request: Request, response: Response):
    # token from cookie or auth header
    auth = request.headers.get("Authorization") or ""
    token = auth.replace("Bearer ", "") if auth else request.cookies.get("auth_token")
    if token:
        invalidate_token(token)
    cookie = f"auth_token=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax"
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

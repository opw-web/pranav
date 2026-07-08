import json
import urllib.error
import urllib.parse
import urllib.request

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.auth import session as session_mod
from app.config import settings
from app.database import get_scoped_db
from app.services.onboarding import ensure_onboarded
from app.templating import templates

router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": request.query_params.get("error")})


@router.get("/auth/google")
async def auth_google_start(request: Request):
    verifier, challenge = session_mod.generate_pkce_pair()
    params = {
        "provider": "google",
        "code_challenge": challenge,
        "code_challenge_method": "s256",
        "redirect_to": settings.google_redirect_url,
    }
    url = f"{settings.supabase_url}/auth/v1/authorize?" + urllib.parse.urlencode(params)
    resp = RedirectResponse(url)
    secure = session_mod.is_secure_request(request)
    resp.set_cookie(
        session_mod.PKCE_COOKIE, verifier, httponly=True, secure=secure, samesite="lax", path="/", max_age=600
    )
    return resp


@router.get("/auth/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    error = request.query_params.get("error_description") or request.query_params.get("error")
    verifier = request.cookies.get(session_mod.PKCE_COOKIE)

    if error or not code or not verifier:
        return RedirectResponse(f"/login?error={urllib.parse.quote(error or 'missing_code')}")

    token_req = urllib.request.Request(
        f"{settings.supabase_url}/auth/v1/token?grant_type=pkce",
        data=json.dumps({"auth_code": code, "code_verifier": verifier}).encode(),
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(token_req, timeout=10) as r:
            token_data = json.loads(r.read())
    except urllib.error.HTTPError:
        return RedirectResponse("/login?error=token_exchange_failed")

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    user_id = token_data["user"]["id"]

    async for db in get_scoped_db(user_id):
        await ensure_onboarded(db, user_id)

    resp = RedirectResponse("/", status_code=302)
    secure = session_mod.is_secure_request(request)
    session_mod.set_session_cookies(resp, access_token, refresh_token, secure=secure)
    resp.delete_cookie(session_mod.PKCE_COOKIE, path="/")
    return resp


@router.get("/logout")
async def logout(request: Request):
    resp = RedirectResponse("/login")
    session_mod.clear_session_cookies(resp)
    return resp

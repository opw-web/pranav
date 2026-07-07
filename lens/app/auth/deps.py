import json
import urllib.request
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, Request, Response

from app.auth import session as session_mod
from app.config import settings
from app.database import get_scoped_db


@dataclass
class CurrentUser:
    id: str
    email: str | None


def _refresh_access_token(refresh_token: str) -> dict | None:
    req = urllib.request.Request(
        f"{settings.supabase_url}/auth/v1/token?grant_type=refresh_token",
        data=json.dumps({"refresh_token": refresh_token}).encode(),
        headers={"apikey": settings.supabase_anon_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


async def get_current_user(request: Request, response: Response) -> CurrentUser:
    """Verifies the Supabase JWT and extracts user_id (= auth.uid()), per §2.3 step 4.
    Transparently refreshes an expired access token using the refresh token cookie."""
    access_token = request.cookies.get(session_mod.ACCESS_COOKIE)
    refresh_token = request.cookies.get(session_mod.REFRESH_COOKIE)

    claims = None
    if access_token:
        try:
            claims = session_mod.verify_access_token(access_token)
        except jwt.PyJWTError:
            claims = None

    if claims is None and refresh_token:
        refreshed = _refresh_access_token(refresh_token)
        if refreshed and "access_token" in refreshed:
            session_mod.set_session_cookies(
                response,
                refreshed["access_token"],
                refreshed["refresh_token"],
                secure=session_mod.is_secure_request(request),
            )
            try:
                claims = session_mod.verify_access_token(refreshed["access_token"])
            except jwt.PyJWTError:
                claims = None

    if claims is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return CurrentUser(id=claims["sub"], email=claims.get("email"))


async def get_scoped_session(user: CurrentUser = Depends(get_current_user)):
    """DB session for the current request: app-level scope (user.id) is layered
    on top of real Postgres RLS (see database.get_scoped_db). Two layers, per §2.3."""
    async for db_session in get_scoped_db(user.id):
        yield db_session

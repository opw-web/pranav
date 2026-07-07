import base64
import hashlib
import secrets
import time
import urllib.request
import json as _json

import jwt

from app.config import settings

ACCESS_COOKIE = "sb_access_token"
REFRESH_COOKIE = "sb_refresh_token"
PKCE_COOKIE = "sb_pkce_verifier"

_jwks_cache: dict = {"keys": [], "fetched_at": 0}
_JWKS_TTL = 3600


def _fetch_jwks() -> dict:
    now = time.time()
    if _jwks_cache["keys"] and now - _jwks_cache["fetched_at"] < _JWKS_TTL:
        return _jwks_cache
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = _json.loads(resp.read())
    _jwks_cache["keys"] = data["keys"]
    _jwks_cache["fetched_at"] = now
    return _jwks_cache


def verify_access_token(token: str) -> dict:
    """Verify a Supabase-issued JWT locally against the project's JWKS (ES256).
    Raises jwt.PyJWTError on any invalid/expired/mismatched-signature token."""
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    jwks = _fetch_jwks()
    matching = [k for k in jwks["keys"] if k.get("kid") == kid]
    if not matching:
        # kid rotated since our cache: force refresh once.
        _jwks_cache["fetched_at"] = 0
        jwks = _fetch_jwks()
        matching = [k for k in jwks["keys"] if k.get("kid") == kid]
    if not matching:
        raise jwt.InvalidTokenError("Unknown signing key")
    public_key = jwt.PyJWK.from_dict(matching[0]).key
    claims = jwt.decode(token, key=public_key, algorithms=["ES256"], audience="authenticated")
    return claims


def is_secure_request(request) -> bool:
    return request.url.scheme == "https"


def set_session_cookies(response, access_token: str, refresh_token: str, secure: bool):
    response.set_cookie(ACCESS_COOKIE, access_token, httponly=True, secure=secure, samesite="lax", path="/")
    response.set_cookie(REFRESH_COOKIE, refresh_token, httponly=True, secure=secure, samesite="lax", path="/")


def clear_session_cookies(response):
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def generate_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge

"""DB access over HTTPS (port 443) — a workaround for dev networks that firewall the
Postgres ports (5432/6543). Production (Vercel) uses the normal asyncpg pooler path;
this module is ONLY for local verification/seeding when raw Postgres is unreachable.

Two channels:
  - rest_*  : Supabase PostgREST data API with the service_role key. Always available.
              Handles insert/select/delete of table rows (bypasses RLS — test harness only).
  - run_sql : Supabase Management API `database/query` — runs ARBITRARY SQL (window
              functions, percentiles, DDL). Requires SUPABASE_ACCESS_TOKEN (a personal
              access token, sbp_...) in the environment. Raises if the token is absent.
"""

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(_ENV_PATH)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROJECT_REF = SUPABASE_URL.split("//", 1)[1].split(".", 1)[0]
ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN")

_REST = SUPABASE_URL + "/rest/v1"
_REST_HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
}


def _call(url: str, method: str, headers: dict, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url} -> {e.code}: {e.read().decode()[:300]}") from None


def rest_select(table: str, query: str = "") -> list:
    q = f"?{query}" if query else ""
    _, data = _call(f"{_REST}/{table}{q}", "GET", _REST_HEADERS)
    return data or []


def rest_insert(table: str, rows) -> list:
    headers = dict(_REST_HEADERS, Prefer="return=representation")
    _, data = _call(f"{_REST}/{table}", "POST", headers, rows)
    return data or []


def rest_delete(table: str, query: str):
    _call(f"{_REST}/{table}?{query}", "DELETE", _REST_HEADERS)


def run_sql(sql: str):
    """Arbitrary SQL over 443 via the Management API. Needs SUPABASE_ACCESS_TOKEN."""
    if not ACCESS_TOKEN:
        raise RuntimeError(
            "SUPABASE_ACCESS_TOKEN not set. Create a personal access token at "
            "https://supabase.com/dashboard/account/tokens and add it to .env to run "
            "arbitrary SQL over HTTPS (needed only when Postgres ports are firewalled)."
        )
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    _, data = _call(url, "POST", headers, {"query": sql})
    return data


if __name__ == "__main__":
    # smoke test the always-available REST channel
    accts = rest_select("accounts", "select=id,name&limit=1")
    print("REST channel OK:", accts)
    if ACCESS_TOKEN:
        print("Management API channel OK:", run_sql("select 1 as ok"))
    else:
        print("Management API channel: no token (set SUPABASE_ACCESS_TOKEN to enable arbitrary SQL over 443)")

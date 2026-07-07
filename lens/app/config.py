import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    supabase_url: str = os.environ["SUPABASE_URL"]
    supabase_anon_key: str = os.environ["SUPABASE_ANON_KEY"]
    supabase_service_role_key: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    database_url: str = os.environ["DATABASE_URL"]
    session_secret: str = os.environ["SESSION_SECRET"]
    google_redirect_url: str = os.environ.get("GOOGLE_REDIRECT_URL", "http://localhost:8000/auth/callback")


settings = Settings()

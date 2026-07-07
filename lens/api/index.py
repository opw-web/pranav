"""Vercel serverless entrypoint. Vercel's @vercel/python runtime serves the ASGI `app`.
The whole FastAPI app is stateless request/response, which is exactly what serverless wants."""

import os
import sys

# ensure the project root (which contains the `app` package) is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

__all__ = ["app"]

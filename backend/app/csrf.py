import os
import secrets
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware

CSRF_TOKEN_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"

CSRF_EXEMPT_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/csrf-token",
    "/supabase/verify-email",
    "/supabase/request-password-reset",
    "/supabase/register",
    # "/supabase/login" - intentionally NOT exempt (uses form-data + cookies)
    "/supabase/refresh",
    "/supabase/logout",
    "/supabase/reset-password",
    "/supabase/change-password",
}

# Allow disabling CSRF for testing
CSRF_ENABLED = os.getenv("CSRF_ENABLED", "true").lower() == "true"

class CSRFMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str | None = None):
        super().__init__(app)
        self.secret_key = secret_key or os.getenv("CSRF_SECRET_KEY", secrets.token_urlsafe(32))

    async def dispatch(self, request: Request, call_next):
        if not CSRF_ENABLED:
            return await call_next(request)

        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return await call_next(request)

        path = request.url.path
        if path in CSRF_EXEMPT_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        csrf_token_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_token_header = request.headers.get(CSRF_HEADER_NAME)

        if not csrf_token_cookie or not csrf_token_header:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing"}
            )

        if not secrets.compare_digest(csrf_token_cookie, csrf_token_header):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid CSRF token"}
            )

        response = await call_next(request)
        return response


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )
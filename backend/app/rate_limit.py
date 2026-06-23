from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    headers_enabled=False,
)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    retry_after = 60
    if exc.limit and hasattr(exc.limit, 'limit'):
        retry_after = exc.limit.limit.get_expiry()
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please try again later."
        },
        headers={"Retry-After": str(retry_after)}
    )

def setup_rate_limiting(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    return limiter
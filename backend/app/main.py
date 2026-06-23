import os
import logging
import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Sentry
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    logger.info("Sentry initialized")

from app.routers import meetups, users, supabase_auth
from app.rate_limit import setup_rate_limiting, limiter
from app.csrf import CSRFMiddleware, generate_csrf_token, set_csrf_cookie

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

setup_rate_limiting(app)

FRONTEND_ORIGIN = os.getenv("FRONTEND_URL", "http://localhost:8081")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*", "X-CSRF-Token"],
    expose_headers=["X-CSRF-Token"],
)

app.add_middleware(CSRFMiddleware)

app.include_router(meetups.router)
app.include_router(users.router)
# app.include_router(register.router)  # DIY auth - commented out
# app.include_router(login.router)     # DIY auth - commented out
app.include_router(supabase_auth.router)

@app.get("/")
@limiter.limit("60/minute")
def greet(request: Request):
    return {"message": "Welcome to Chaatly"}

@app.get("/csrf-token")
@limiter.limit("30/minute")
def get_csrf_token(request: Request, response: Response):
    token = generate_csrf_token()
    set_csrf_cookie(response, token)
    return {"csrf_token": token}
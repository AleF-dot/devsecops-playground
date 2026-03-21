from fastapi import FastAPI, Request
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from db import get_connection, init_db
import datetime
import secrets
import requests
import os

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


EVENT_API_KEY = os.environ.get("EVENT_API_KEY")

conn = get_connection()
if conn is not None:
            init_db(conn)
else:
    raise Exception("Database connection missing")

class LoginRequest(BaseModel):
    user: str
    password : str

@app.get("/health")
def health():
    return {"status": "ok", "service": "auth", "time": datetime.datetime.now().replace(microsecond=0).isoformat()}

@app.post("/login")
@limiter.limit("5/minute")
def login(request: Request, body: LoginRequest):
    user = body.user
    
    if not users.get(user):
        return {"success": False, "reason": "not found"}
    
    if users_states.get(user) == "blocked":
        requests.post(
            "http://event-service:8001/event",
            json={"type": "login_blocked", "user": user},
            headers={"X-Api-Key": EVENT_API_KEY}
        )
        return {"success": False, "reason": "blocked"}

    if users.get(user) == body.password:
        token = secrets.token_hex(nbytes=15)
        sessions[token] = user
        requests.post(
            "http://event-service:8001/event",
            json={"type": "login_succeeded", "user": user},
            headers={"X-Api-Key": EVENT_API_KEY}
        )
        return {"success": True, "token" : token}
    else:
        attempts[user] = attempts.get(user, 0) + 1
        if attempts[user] == 3:
            users_states[user] = "blocked"
        requests.post(
            "http://event-service:8001/event",
            json={"type": "login_failed", "user": user},
            headers={"X-Api-Key": EVENT_API_KEY}
        )
        return {"success": False, "reason": "invalid password"}


@app.get("/validate")
def validate_token(token: str):
    if sessions.get(token):
        return {"success": True, "user": sessions[token]}
    else:
        return {"success": False, "reason": "invalid token"}
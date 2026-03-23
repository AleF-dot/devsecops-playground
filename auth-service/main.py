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
    
    with conn.cursor() as cur:
        cur.execute("SELECT password, status FROM users WHERE username = %s", (user,))
        user_row = cur.fetchone()
        cur.execute("SELECT attempts FROM attempts WHERE username = %s", (user,))
        attempts_row = cur.fetchone()
    
    if not user_row:
        return {"success": False, "reason": "not found"}
    
    if user_row[1] == "blocked":
        requests.post(
            "http://event-service:8001/event",
            json={"type": "login_blocked", "user": user},
            headers={"X-Api-Key": EVENT_API_KEY}
        )
        return {"success": False, "reason": "blocked"}

    if user_row[0] == body.password:
        token = secrets.token_hex(nbytes=15)
        with conn.cursor() as cur:
            cur.execute("INSERT INTO sessions (token, username) VALUES (%s, %s)", (token, user,))
        conn.commit()
        requests.post(
            "http://event-service:8001/event",
            json={"type": "login_succeeded", "user": user},
            headers={"X-Api-Key": EVENT_API_KEY}
        )
        return {"success": True, "token" : token}
    else:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO attempts (username, attempts) VALUES (%s, 1) ON CONFLICT (username) DO UPDATE SET attempts = attempts.attempts + 1",
                (user,)
            )
            if attempts_row and attempts_row[0] == 2:
                cur.execute("UPDATE users SET status = 'blocked' WHERE username = %s", (user,))
        conn.commit()
        requests.post(
            "http://event-service:8001/event",
            json={"type": "login_failed", "user": user},
            headers={"X-Api-Key": EVENT_API_KEY}
        )
        return {"success": False, "reason": "invalid password"}


@app.get("/validate")
def validate_token(token: str):
    
    with conn.cursor() as cur:
        cur.execute("SELECT username FROM sessions WHERE token = %s", (token,))
        session_row = cur.fetchone()
    
    if session_row:
        return {"success": True, "user": session_row[0]}
    else:
        return {"success": False, "reason": "invalid token"}
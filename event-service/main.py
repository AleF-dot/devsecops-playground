from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import datetime
import requests
import os
import hmac

KEY = os.environ.get("EVENT_API_KEY")
ALERT_API_KEY = os.environ.get("ALERT_API_KEY")

app = FastAPI()

events = []

class Event(BaseModel):
    type: str
    user: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "event", "time": datetime.datetime.now().replace(microsecond=0).isoformat()}

@app.post("/event")
def event_handler(event: Event, x_api_key: str = Header(...)):
    if hmac.compare_digest(x_api_key, KEY):
        events.append({
            "type": event.type,
            "user": event.user,
            "time": datetime.datetime.now().replace(microsecond=0).isoformat()
        })
        if event.type == "login_failed":
            requests.post(
                "http://alert-service:8002/alert",
                json={
                    "type": event.type,
                    "user": event.user,
                },
                headers={"X-Api-Key": ALERT_API_KEY}
            )
        return {"success": True}
    else:
        raise HTTPException(status_code=401, detail="invalid API key")

@app.get("/events")
def return_events(x_api_key: str = Header(...)):
    if hmac.compare_digest(x_api_key, KEY):
        return {"success": True, "events": events}
    else:
        raise HTTPException(status_code=401, detail="invalid API key")

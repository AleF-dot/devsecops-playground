from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import datetime
import os
import hmac

KEY = os.environ.get("ALERT_API_KEY")

app = FastAPI()

events = []

alerts = []

class Event(BaseModel):
    type: str
    user: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "alert", "time": datetime.datetime.now().replace(microsecond=0).isoformat()}

@app.post("/alert")
def alert_handler(event: Event, x_api_key: str = Header(...)):
    if hmac.compare_digest(x_api_key, KEY):
        events.append({
            "type": event.type,
            "user": event.user,
            "time": datetime.datetime.now().replace(microsecond=0).isoformat()
            })
        filtered_events = [e for e in events if e["user"] == event.user and datetime.datetime.fromisoformat(e["time"]) >= datetime.datetime.now() - datetime.timedelta(seconds=60)]
        if len(filtered_events) > 2:
            alert = {
                "alert": f'user "{event.user}" compromised',
                "last_event": event
                }
            alerts.append(alert)
            return {"success": True, "alert": alert}
        else:
            return {"success": True, "alert": False}
    else:
        raise HTTPException(status_code=401, detail="invalid API key")

@app.get("/alerts")
def return_alerts(x_api_key: str = Header(...)):
    if hmac.compare_digest(x_api_key, KEY):
        return {"success": True, "alerts": alerts}
    else:
        raise HTTPException(status_code=401, detail="invalid API key")
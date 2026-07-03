from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mangum import Mangum
from pydantic import BaseModel
import os
import requests

app = FastAPI(title="ServiceNow Integration")
templates = Jinja2Templates(directory="servicenow_app/templates")
handler = Mangum(app)

SNOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE", "").rstrip("/")
SNOW_USERNAME = os.getenv("SERVICENOW_USERNAME", "")
SNOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD", "")


class IncidentCreate(BaseModel):
    short_description: str
    description: str
    urgency: str = "3"
    impact: str = "3"
    category: str = "inquiry"


class IncidentResponse(BaseModel):
    number: str | None = None
    short_description: str | None = None
    state: str | None = None
    sys_id: str | None = None


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/health")
async def health_route():
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/incidents", response_model=list[IncidentResponse])
async def list_incidents():
    if not all([SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD]):
        raise HTTPException(status_code=500, detail="ServiceNow credentials are not configured")

    response = requests.get(
        f"{SNOW_INSTANCE}/api/now/table/incident",
        params={"sysparm_limit": 10, "active": True},
        auth=(SNOW_USERNAME, SNOW_PASSWORD),
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    return [
        IncidentResponse(
            number=item.get("number"),
            short_description=item.get("short_description"),
            state=item.get("state"),
            sys_id=item.get("sys_id"),
        )
        for item in payload.get("result", [])
    ]


@app.post("/api/incidents", response_model=IncidentResponse)
async def create_incident(payload: IncidentCreate):
    if not all([SNOW_INSTANCE, SNOW_USERNAME, SNOW_PASSWORD]):
        raise HTTPException(status_code=500, detail="ServiceNow credentials are not configured")

    response = requests.post(
        f"{SNOW_INSTANCE}/api/now/table/incident",
        json={
            "short_description": payload.short_description,
            "description": payload.description,
            "urgency": payload.urgency,
            "impact": payload.impact,
            "category": payload.category,
        },
        auth=(SNOW_USERNAME, SNOW_PASSWORD),
        timeout=15,
    )
    response.raise_for_status()
    result = response.json().get("result", {})
    return IncidentResponse(
        number=result.get("number"),
        short_description=result.get("short_description"),
        state=result.get("state"),
        sys_id=result.get("sys_id"),
    )

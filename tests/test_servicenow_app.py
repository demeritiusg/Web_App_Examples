from fastapi.testclient import TestClient
from unittest.mock import patch
import importlib

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

app_module = importlib.import_module("servicenow_app.main")
client = TestClient(app_module.app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("servicenow_app.main.requests.get")
def test_list_incidents_uses_credentials(mock_get):
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.json.return_value = {"result": [{"number": "INC001", "short_description": "Test", "state": "Active", "sys_id": "abc"}]}

    with patch.dict("os.environ", {"SERVICENOW_INSTANCE": "https://example.service-now.com", "SERVICENOW_USERNAME": "user", "SERVICENOW_PASSWORD": "pass"}, clear=False):
        importlib.reload(app_module)
        response = client.get("/api/incidents")

    assert response.status_code == 200
    assert response.json()[0]["number"] == "INC001"


@patch("servicenow_app.main.requests.post")
def test_create_incident(mock_post):
    mock_post.return_value.raise_for_status.return_value = None
    mock_post.return_value.json.return_value = {"result": {"number": "INC002", "short_description": "Created", "state": "New", "sys_id": "def"}}

    with patch.dict("os.environ", {"SERVICENOW_INSTANCE": "https://example.service-now.com", "SERVICENOW_USERNAME": "user", "SERVICENOW_PASSWORD": "pass"}, clear=False):
        importlib.reload(app_module)
        response = client.post(
            "/api/incidents",
            json={"short_description": "Created", "description": "Created via test", "urgency": "1", "impact": "1"},
        )

    assert response.status_code == 200
    assert response.json()["number"] == "INC002"

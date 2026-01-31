
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from python_service.core.errors import KongError, KongAuthError
from python_service.main import app
# We import main app. But app startup might trigger things. 
# Better to create a test app or assume main app is clean enough.
# Let's try separate TestClient(app).

client = TestClient(app)

# Inject a test route that raises KongError
@app.get("/test/error")
def trigger_error():
    raise KongError("Generic error", code="TEST_ERR", status_code=418, details={"foo": "bar"})

@app.get("/test/auth_error")
def trigger_auth_error():
    raise KongAuthError("Invalid key")

def test_structured_error_format():
    response = client.get("/test/error")
    assert response.status_code == 418
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "TEST_ERR"
    assert data["error"]["message"] == "Generic error"
    assert data["error"]["details"] == {"foo": "bar"}

def test_auth_error_format():
    response = client.get("/test/auth_error")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "AUTH_FAILED"
    assert data["error"]["message"] == "Invalid key"

def test_kong_error_class():
    err = KongError("msg", code="CODE", status_code=400, details="det")
    assert err.status_code == 400
    d = err.to_dict()
    assert d["error"]["code"] == "CODE"

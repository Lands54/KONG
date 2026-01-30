import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200

def test_config_check_api():
    """测试脱敏后的配置检查接口"""
    response = client.get("/api/v1/config/check")
    assert response.status_code == 200
    data = response.json()
    assert "api_key" in data
    assert "ready_instances" in data # 确保新字段存在
    assert isinstance(data["ready_instances"], list)

def test_get_catalog():
    response = client.get("/api/v1/models/catalog")
    assert response.status_code == 200
    assert "extractors" in response.json()["catalog"]

def test_inference_api_e2e():
    payload = {
        "goal": "Test",
        "text": "Hello world",
        "orchestrator": "fuzz_test",
        "params": {"node_count": 2}
    }
    response = client.post("/api/v1/infer", json=payload)
    assert response.status_code == 200
    assert "graph" in response.json()

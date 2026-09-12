from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert 'status' in response.json()


def test_ready_endpoint():
    response = client.get('/ready')
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data


def test_live_endpoint():
    response = client.get('/live')
    assert response.status_code == 200
    assert response.json()['status'] == 'ALIVE'


def test_metrics_endpoint():
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'counters' in response.json()


def test_diagnostics_endpoint():
    response = client.get('/api/v1/admin/diagnostics')
    assert response.status_code == 200

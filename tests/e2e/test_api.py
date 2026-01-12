from fastapi.testclient import TestClient
from oceanus_agent.api.app import app
from oceanus_agent.config.settings import settings

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["environment"] == settings.app.env

def test_readiness_check_mocked(mocker):
    """Test readiness check with mocked DB."""
    # Mock MySQLService
    mock_service = mocker.patch("oceanus_agent.api.routes.MySQLService")
    mock_instance = mock_service.return_value
    
    # Mock async context manager for session
    mock_session = mocker.AsyncMock()
    mock_instance.async_session.return_value.__aenter__.return_value = mock_session
    
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_readiness_check_failure(mocker):
    """Test readiness check failure."""
    mock_service = mocker.patch("oceanus_agent.api.routes.MySQLService")
    mock_instance = mock_service.return_value
    mock_instance.async_session.side_effect = Exception("DB Connection Failed")
    
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert "Database not ready" in response.json()["detail"]

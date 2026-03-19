import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from soc.api.main import app, USERS_DB, create_access_token

client = TestClient(app)

@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin", "role": "admin"})

@patch("soc.api.main.ResponderAgent")
def test_approve_action_valid(mock_responder_class, admin_token):
    mock_responder = mock_responder_class.return_value
    mock_responder.approve_action.return_value = True
    
    action_id = "test-action-123"
    response = client.post(
        f"/approve/{action_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_responder.approve_action.assert_called_once_with(action_id)

@patch("soc.api.main.ResponderAgent")
def test_approve_action_invalid_format(mock_responder_class, admin_token):
    mock_responder = mock_responder_class.return_value
    
    # Invalid characters ($ not allowed in our regex ^[a-zA-Z0-9-]+$)
    action_id = "invalid$action"
    response = client.post(
        f"/approve/{action_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 400
    assert "Invalid Action ID format" in response.json()["detail"]
    mock_responder.approve_action.assert_not_called()

@patch("soc.api.main.ResponderAgent")
def test_approve_action_not_found(mock_responder_class, admin_token):
    mock_responder = mock_responder_class.return_value
    mock_responder.approve_action.return_value = False
    
    action_id = "non-existent-id"
    response = client.post(
        f"/approve/{action_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404
    assert "not found or already approved" in response.json()["detail"]
    mock_responder.approve_action.assert_called_once_with(action_id)

def test_approve_action_unauthorized():
    action_id = "some-id"
    response = client.post(f"/approve/{action_id}")
    assert response.status_code == 401

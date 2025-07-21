# ================================
# tests/test_auth.py
# ================================

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_health_endpoint(client):
    """Test endpoint de salud"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint(client):
    """Test endpoint raíz"""
    response = client.get("/")
    assert response.status_code == 200
    assert "CMS Dinámico API" in response.json()["message"]

@patch('app.auth.middleware.ClerkAuthMiddleware.verify_clerk_token')
def test_protected_endpoint_without_auth(mock_verify, client):
    """Test endpoint protegido sin autenticación"""
    response = client.get("/api/auth/me")
    assert response.status_code == 401

@patch('app.auth.middleware.ClerkAuthMiddleware.verify_clerk_token')
def test_protected_endpoint_with_auth(mock_verify, client):
    """Test endpoint protegido con autenticación"""
    mock_verify.return_value = {"user_id": "test_123"}
    
    headers = {"Authorization": "Bearer test_token"}
    
    with patch('app.services.user_service.UserService.get_user_by_clerk_id') as mock_get_user:
        mock_get_user.return_value = None
        
        response = client.get("/api/auth/me", headers=headers)
        # Debería fallar porque no encuentra el usuario en la BD
        assert response.status_code == 404
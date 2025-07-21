# ================================
# tests/test_api_service.py
# ================================

import pytest
from unittest.mock import AsyncMock, patch
from app.services.api_service import ApiService
from app.models.api_config import ApiConfiguration, ApiConfigData, AuthConfig

@pytest.mark.asyncio
async def test_api_service_request():
    """Test realizar petición a API externa"""
    service = ApiService()
    
    # Mock de configuración
    mock_config = ApiConfiguration(
        business_id="test_business",
        api_name="test_api",
        configuracion=ApiConfigData(
            nombre="Test API",
            base_url="https://api.test.com",
            auth=AuthConfig(tipo="bearer", token="test_token"),
            endpoints={"clientes": "/customers"}
        )
    )
    
    # Mock del cliente HTTP
    with patch.object(service, 'get_api_config', return_value=mock_config):
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"data": "test"}
            mock_response.status_code = 200
            mock_response.raise_for_status = AsyncMock()
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await service.make_request(
                "test_business",
                "test_api", 
                "/customers",
                use_cache=False
            )
            
            assert result == {"data": "test"}


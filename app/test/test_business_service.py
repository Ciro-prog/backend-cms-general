import pytest
from app.services.business_service import BusinessService
from app.models.business import BusinessTypeCreate, BusinessInstanceCreate

@pytest.mark.asyncio
async def test_create_business_type(test_db):
    """Test crear business type"""
    service = BusinessService()
    
    business_type_data = BusinessTypeCreate(
        tipo="test_isp",
        nombre="Test ISP",
        descripcion="ISP para testing",
        componentes_base=[
            {
                "id": "whatsapp",
                "nombre": "WhatsApp",
                "tipo": "integration",
                "obligatorio": True
            }
        ]
    )
    
    business_type = await service.create_business_type(business_type_data)
    
    assert business_type.tipo == "test_isp"
    assert business_type.nombre == "Test ISP"
    assert len(business_type.componentes_base) == 1

@pytest.mark.asyncio
async def test_get_business_type_by_tipo(test_db):
    """Test obtener business type por tipo"""
    service = BusinessService()
    
    # Crear business type
    business_type_data = BusinessTypeCreate(
        tipo="test_clinica",
        nombre="Test Clínica"
    )
    await service.create_business_type(business_type_data)
    
    # Obtener business type
    found_type = await service.get_business_type_by_tipo("test_clinica")
    
    assert found_type is not None
    assert found_type.tipo == "test_clinica"
    assert found_type.nombre == "Test Clínica"

@pytest.mark.asyncio
async def test_create_business_instance(test_db):
    """Test crear business instance"""
    service = BusinessService()
    
    # Crear business type primero
    business_type_data = BusinessTypeCreate(
        tipo="test_tienda",
        nombre="Test Tienda"
    )
    await service.create_business_type(business_type_data)
    
    # Crear business instance
    business_data = BusinessInstanceCreate(
        business_id="test_tienda_001",
        nombre="Mi Tienda Test",
        tipo_base="test_tienda"
    )
    
    business = await service.create_business_instance(business_data)
    
    assert business.business_id == "test_tienda_001"
    assert business.nombre == "Mi Tienda Test"
    assert business.tipo_base == "test_tienda"


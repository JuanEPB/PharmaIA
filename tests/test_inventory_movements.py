import pytest

from app.services.inventory_movement_service import InventoryMovementService


def test_entrada_incrementa_stock():
    assert InventoryMovementService.calculate_new_stock("ENTRADA", 10, 5) == 15


def test_devolucion_incrementa_stock():
    assert InventoryMovementService.calculate_new_stock("DEVOLUCION", 10, 3) == 13


def test_salida_disminuye_stock():
    assert InventoryMovementService.calculate_new_stock("SALIDA", 10, 4) == 6


def test_caducidad_disminuye_stock():
    assert InventoryMovementService.calculate_new_stock("CADUCIDAD", 10, 2) == 8


def test_ajuste_establece_stock_final():
    assert InventoryMovementService.calculate_new_stock("AJUSTE", 10, 25) == 25


def test_no_permite_stock_negativo():
    with pytest.raises(ValueError, match="stock negativo"):
        InventoryMovementService.calculate_new_stock("SALIDA", 2, 5)


def test_no_permite_cantidad_cero():
    with pytest.raises(ValueError, match="mayor que cero"):
        InventoryMovementService.validate_quantity(0)

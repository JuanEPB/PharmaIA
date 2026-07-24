from app.database.repositories.catalogo_repository import (
    CatalogoRepository,
)
from app.database.repositories.medicamentos_repository import (
    MedicamentosRepository,
)


class InventoryService:
    """
    Servicio central del inventario.
    """

    def obtener_todos(self):
        return MedicamentosRepository.obtener_todos()

    def obtener_inventario_detallado(self):
        return CatalogoRepository.obtener_inventario_detallado()

    def obtener_bajo_stock(self):
        return MedicamentosRepository.obtener_bajo_stock()

    def obtener_agotados(self):
        return MedicamentosRepository.obtener_agotados()

    def buscar(self, nombre):
        return MedicamentosRepository.buscar(nombre)

    def obtener_caducados(self):
        return MedicamentosRepository.obtener_caducados()

    def obtener_por_caducar(self, dias=30):
        dias = self._normalizar_dias(dias)

        return MedicamentosRepository.obtener_por_caducar(
            dias
        )

    def obtener_caducidad_mes_actual(self):
        return (
            MedicamentosRepository
            .obtener_caducidad_mes_actual()
        )

    def obtener_resumen(self):
        return MedicamentosRepository.obtener_resumen()

    def buscar_por_categoria(self, categoria):
        return CatalogoRepository.buscar_por_categoria(
            categoria
        )

    def buscar_por_proveedor(self, proveedor):
        return CatalogoRepository.buscar_por_proveedor(
            proveedor
        )

    def obtener_resumen_por_categoria(self):
        return (
            CatalogoRepository
            .obtener_resumen_por_categoria()
        )

    def obtener_resumen_por_proveedor(self):
        return (
            CatalogoRepository
            .obtener_resumen_por_proveedor()
        )

    def obtener_medicamento_mas_caro(self):
        return (
            CatalogoRepository
            .obtener_medicamento_mas_caro()
        )

    def obtener_medicamento_mas_barato(self):
        return (
            CatalogoRepository
            .obtener_medicamento_mas_barato()
        )

    def obtener_medicamento_menor_stock(self):
        return (
            CatalogoRepository
            .obtener_medicamento_menor_stock()
        )

    def obtener_medicamento_mayor_stock(self):
        return (
            CatalogoRepository
            .obtener_medicamento_mayor_stock()
        )

    def proveedores_con_caducidad(self, dias=30):
        dias = self._normalizar_dias(dias)

        return CatalogoRepository.proveedores_con_caducidad(
            dias
        )

    @staticmethod
    def _normalizar_dias(dias):
        try:
            dias = int(dias)
        except (TypeError, ValueError):
            dias = 30

        return max(
            1,
            min(dias, 365),
        )


inventory_service = InventoryService()

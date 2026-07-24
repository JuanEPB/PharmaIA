from app.database.repositories.medicamentos_repository import (
    MedicamentosRepository,
)


class InventoryService:
    """
    Capa de servicio para las operaciones del inventario.
    """

    def obtener_todos(self):

        return MedicamentosRepository.obtener_todos()

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

    @staticmethod
    def _normalizar_dias(dias):

        try:
            dias = int(dias)
        except (TypeError, ValueError):
            dias = 30

        if dias < 1:
            return 1

        if dias > 365:
            return 365

        return dias


inventory_service = InventoryService()

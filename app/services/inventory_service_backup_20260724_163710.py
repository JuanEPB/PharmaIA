from app.database.repositories.medicamentos_repository import MedicamentosRepository


class InventoryService:

    def obtener_todos(self):

        return MedicamentosRepository.obtener_todos()


    def obtener_bajo_stock(self):

        return MedicamentosRepository.obtener_bajo_stock()


    def obtener_agotados(self):

        return MedicamentosRepository.obtener_agotados()


    def buscar(self, nombre):

        return MedicamentosRepository.buscar(nombre)


inventory_service = InventoryService()

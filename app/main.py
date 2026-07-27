from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.conversation_routes import router as conversation_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.depletion_routes import router as depletion_router
from app.api.inventory_routes import router as inventory_router
from app.api.movement_routes import router as movement_router
from app.routes import router as assistant_router


app = FastAPI(
    title="Pharma Neural Assistant",
    description=(
        "API inteligente para consultas del "
        "inventario farmaceutico."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(assistant_router)


@app.get("/")
def inicio():
    return {
        "nombre": "Pharma Neural Assistant",
        "estado": "activo",
        "version": "1.0.0",
        "documentacion": "/docs",
    }

# Memoria conversacional
app.include_router(conversation_router)

# Dashboard de inventario
app.include_router(inventory_router)

# Dashboard predictivo
app.include_router(dashboard_router)

# Movimientos de inventario
app.include_router(movement_router)

# Predicción de agotamiento
app.include_router(depletion_router)


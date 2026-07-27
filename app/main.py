from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent_routes import router as agent_router
from app.api.anomaly_routes import router as anomaly_router
from app.api.conversation_routes import router as conversation_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.depletion_routes import router as depletion_router
from app.api.inventory_routes import router as inventory_router
from app.api.learning_routes import router as learning_router
from app.api.movement_routes import router as movement_router
from app.api.recommendation_routes import router as recommendation_router
from app.api.report_routes import router as report_router
from app.api.profile_routes import router as profile_router
from app.api.sales_routes import router as sales_router
from app.api.vision_routes import router as vision_router
from app.api.voice_routes import router as voice_router
from app.config.settings import settings
from app.routes import router as assistant_router


app = FastAPI(
    title="Pharma Neural Assistant",
    description=(
        "API inteligente para consultas del "
        "inventario farmaceutico. Version 2."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
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
        "version": "2.0.0",
        "etapa": "Version 2",
        "documentacion": "/docs",
    }

# Memoria conversacional
app.include_router(conversation_router)

# Dashboard de inventario
app.include_router(inventory_router)

# Perfil operativo de la app e IA
app.include_router(profile_router)

# Dashboard predictivo
app.include_router(dashboard_router)

# Movimientos de inventario
app.include_router(movement_router)

# Ventas y tickets
app.include_router(sales_router)

# Detección de anomalías
app.include_router(anomaly_router)

# Recomendaciones automáticas
app.include_router(recommendation_router)

# Reportes IA
app.include_router(report_router)

# Visión artificial
app.include_router(vision_router)

# Voz
app.include_router(voice_router)

# Agente autónomo
app.include_router(agent_router)

# Predicción de agotamiento
app.include_router(depletion_router)

# Aprendizaje por feedback del usuario
app.include_router(learning_router)


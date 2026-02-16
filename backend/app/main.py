"""
FastAPI Application - Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .routes import router
from .database import engine, Base

# Criar tabelas (apenas em desenvolvimento - usar Alembic em produção)
# Base.metadata.create_all(bind=engine)

# Verificar ambiente
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

app = FastAPI(
    title="FastMission - Saneamento Cadastral",
    description="API para auditoria de classificações fiscais (NCM) com IA",
    version="1.0.0",
    docs_url="/docs" if not IS_PRODUCTION else None,  # Desabilita /docs em produção
    redoc_url="/redoc" if not IS_PRODUCTION else None,  # Desabilita /redoc em produção
)

# CORS - Configuração de origens permitidas
origins = [
    "http://localhost:5173",  # Frontend dev (Vite)
    "http://localhost:3000",  # Frontend dev (Next.js)
]

# Em produção, adicionar domínios reais
if IS_PRODUCTION:
    # TODO: Adicionar seu domínio real quando tiver
    production_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    if production_origins and production_origins[0]:
        origins.extend(production_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(router, prefix="/api", tags=["cadastral"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "FastMission API",
        "version": "1.0.0",
        "environment": ENVIRONMENT
    }


@app.get("/health")
async def health():
    """Health check endpoint para monitoramento"""
    return {
        "status": "healthy",
        "environment": ENVIRONMENT
    }

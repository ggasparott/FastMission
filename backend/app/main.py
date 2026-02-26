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
    docs_url="/docs",  # Desabilita /docs em produção
    redoc_url="/redoc",  # Desabilita /redoc em produção
)

# CORS - Configuração dinâmica baseada em variável de ambiente
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173", "")
origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

# Em desenvolvimento, adicionar origens padrão
if not IS_PRODUCTION:
    default_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://luminous-custard-2eed2e.netlify.app/"
    ]
    for origin in default_origins:
        if origin not in origins:
            origins.append(origin)

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

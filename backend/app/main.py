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

app = FastAPI(
    title="FastMission - Saneamento Cadastral",
    description="MVP para auditoria de classificações fiscais (NCM) com IA",
    version="0.1.0"
)

# CORS - Permitir frontend acessar API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # URLs do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(router, prefix="/api", tags=["cadastral"])


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "FastMission API",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

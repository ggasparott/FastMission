"""
Script para inicializar banco de dados
Uso: python scripts/init_db.py
"""
import sys
import os

# Adicionar caminho do backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app.models import Lote, ItemCadastral

def init_db():
    print("🔧 Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas com sucesso!")
    
    # Listar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📊 Tabelas: {', '.join(tables)}")
    
    # Mostrar estrutura de cada tabela
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"\n📋 {table}:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")

if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

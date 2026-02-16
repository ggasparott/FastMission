# FastMission Backend

Backend FastAPI para MVP de Saneamento Cadastral (Auditoria de NCM com IA).

## Setup Rápido

### 1. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com suas configurações
```

### 4. Inicializar banco de dados (com Alembic)

```bash
# Criar primeira migration
alembic revision --autogenerate -m "create initial tables"

# Aplicar migrations
alembic upgrade head
```

### 5. Rodar servidor FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API estará em: http://localhost:8000  
Docs interativa: http://localhost:8000/docs

### 6. Rodar Celery Worker (em outro terminal)

```bash
celery -A app.tasks worker --loglevel=info
```

## Estrutura

```
backend/
├── app/
│   ├── main.py          # Entry point FastAPI
│   ├── database.py      # Configuração SQLAlchemy
│   ├── models.py        # Modelos ORM
│   ├── schemas.py       # Pydantic schemas
│   ├── routes.py        # Endpoints API
│   └── tasks.py         # Celery tasks
├── skills/
│   └── validate_ncm.py  # Script IA (isolado)
├── alembic/             # Migrations
├── requirements.txt     # Dependências
└── .env.example         # Template de variáveis
```

## Endpoints Principais

- `POST /api/upload` - Upload CSV (retorna 202 Accepted)
- `GET /api/lotes/{id}/status` - Checar progresso
- `GET /api/lotes/{id}/itens` - Listar itens processados
- `GET /api/lotes` - Listar todos os lotes

## Desenvolvimento

### Criar nova migration

```bash
alembic revision --autogenerate -m "descrição da mudança"
alembic upgrade head
```

### Reverter migration

```bash
alembic downgrade -1
```

### Testar API manualmente

```bash
# Upload de CSV
curl -X POST http://localhost:8000/api/upload \
  -F "file=@produtos.csv"

# Checar status
curl http://localhost:8000/api/lotes/{id}/status

# Listar itens
curl http://localhost:8000/api/lotes/{id}/itens?apenas_divergentes=true
```

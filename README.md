# FastMission - Saneamento Cadastral MVP

MVP para auditoria de classificações fiscais (NCM) de produtos usando IA, no contexto da Reforma Tributária brasileira (IBS/CBS).

## 🚀 Quick Start

### 1. Subir infraestrutura com Docker

```bash
docker-compose up -d
```

Isso vai subir:
- PostgreSQL (porta 5432)
- Redis (porta 6379)
- Backend FastAPI (porta 8000)
- Celery Worker

### 2. Criar tabelas do banco

```bash
docker-compose exec backend alembic revision --autogenerate -m "create initial tables"
docker-compose exec backend alembic upgrade head
```

### 3. Testar API

```bash
# Health check
curl http://localhost:8000/health

# API docs interativa
# Abrir no navegador: http://localhost:8000/docs

# Upload de CSV de teste
curl -X POST http://localhost:8000/api/upload \
  -F "file=@backend/test_produtos.csv"
```

### 4. Ver logs do worker

```bash
docker-compose logs -f worker
```

## 📁 Estrutura do Projeto

```
FastMission/
├── backend/
│   ├── app/
│   │   ├── main.py          # Entry point FastAPI
│   │   ├── database.py      # SQLAlchemy config
│   │   ├── models.py        # ORM models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routes.py        # API endpoints
│   │   └── tasks.py         # Celery tasks
│   ├── skills/
│   │   └── validate_ncm.py  # IA validation script
│   ├── alembic/             # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── test_produtos.csv    # CSV de teste
├── docker-compose.yml
└── prompt.md               # Especificações do projeto
```

## 🔧 Desenvolvimento Local (sem Docker)

### Backend

```bash
cd backend

# Criar venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env

# Rodar API
uvicorn app.main:app --reload --port 8000

# Rodar worker (outro terminal)
celery -A app.tasks worker --loglevel=info
```

### Serviços externos

```bash
# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=fastmission \
  -e POSTGRES_PASSWORD=senha123 \
  -e POSTGRES_DB=cadastral_db \
  postgres:15

# Redis
docker run -d -p 6379:6379 redis:7-alpine
```

## 📊 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/upload` | Upload CSV (retorna 202 Accepted) |
| GET | `/api/lotes/{id}/status` | Checar progresso do processamento |
| GET | `/api/lotes/{id}/itens` | Listar itens processados |
| GET | `/api/lotes` | Listar todos os lotes |

## 🧪 Testando o Fluxo Completo

```bash
# 1. Fazer upload
LOTE_ID=$(curl -X POST http://localhost:8000/api/upload \
  -F "file=@backend/test_produtos.csv" \
  | jq -r '.lote_id')

# 2. Checar status (rodar várias vezes)
curl http://localhost:8000/api/lotes/$LOTE_ID/status | jq

# 3. Ver itens processados
curl http://localhost:8000/api/lotes/$LOTE_ID/itens | jq

# 4. Ver apenas divergências
curl "http://localhost:8000/api/lotes/$LOTE_ID/itens?apenas_divergentes=true" | jq
```

## 🔍 Debug

### Ver logs

```bash
# Todos os serviços
docker-compose logs -f

# Apenas worker
docker-compose logs -f worker

# Apenas backend
docker-compose logs -f backend
```

### Acessar banco de dados

```bash
docker-compose exec postgres psql -U fastmission -d cadastral_db

# Queries úteis:
SELECT * FROM lotes ORDER BY data_upload DESC LIMIT 5;
SELECT descricao, ncm_original, ncm_sugerido, status_validacao FROM itens_cadastrais LIMIT 10;
```

### Acessar Redis

```bash
docker-compose exec redis redis-cli

# Dentro do redis-cli:
KEYS *
```

## 🛠️ Comandos Úteis

```bash
# Parar tudo
docker-compose down

# Resetar banco (CUIDADO: apaga dados)
docker-compose down -v

# Reconstruir containers
docker-compose up -d --build

# Ver status dos containers
docker-compose ps

# Rodar migration
docker-compose exec backend alembic upgrade head

# Criar nova migration
docker-compose exec backend alembic revision --autogenerate -m "descrição"
```

## ⚠️ Notas Importantes

### NCM como String
NCM é sempre `String` no banco, nunca `Integer`. Exemplo: `"0102.31.00"` começa com zero.

### Processamento Assíncrono
Upload retorna `202 Accepted` imediatamente. Worker processa em background. Frontend deve fazer polling do status.

### Script de IA Isolado
`skills/validate_ncm.py` roda via subprocess, **não** inline no código da API. Facilita testes e troca de LLM.

### Mock para MVP
Script de IA atual usa regras simples (mock). Depois você integra OpenAI/Claude/outro LLM.

## 📝 Próximos Passos

- [ ] Integrar LLM real em `skills/validate_ncm.py`
- [ ] Criar frontend React
- [ ] Adicionar autenticação
- [ ] Exportar relatórios

## 📄 Licença

MIT
# FastMission

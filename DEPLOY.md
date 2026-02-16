# 🚀 Guia de Deploy - FastMission

## 📋 Arquivos Criados para Produção

✅ `docker-compose.prod.yml` - Configuração Docker para produção
✅ `backend/.dockerignore` - Arquivos que não vão para a imagem Docker
✅ `.env.example` - Template de variáveis de ambiente
✅ `.env` - Variáveis locais (NÃO commitado no Git)
✅ `.gitignore` - Arquivos ignorados pelo Git
✅ `test_upload.csv` - Arquivo CSV de teste

## 🧪 Testar Localmente (ANTES de subir para Easypanel)

### 1. Subir ambiente de produção local

```bash
# Parar docker dev (se estiver rodando)
docker-compose down

# Subir com configuração de produção
docker-compose -f docker-compose.prod.yml up --build
```

**Aguarde aparecer:**
- ✅ postgres ... healthy
- ✅ redis ... healthy
- ✅ backend ... started
- ✅ worker ... started

### 2. Aplicar migrations (em outro terminal)

```bash
# Criar migration inicial
docker exec fastmission-backend alembic revision --autogenerate -m "Initial tables"

# Aplicar no banco
docker exec fastmission-backend alembic upgrade head

# Verificar tabelas criadas
docker exec fastmission-postgres psql -U fastmission -d cadastral_db -c "\dt"
```

### 3. Testar API

```bash
# Health check
curl http://localhost:8000/health

# Resultado esperado:
# {"status":"healthy","environment":"production"}

# Testar upload
curl -X POST http://localhost:8000/api/upload -F "file=@test_upload.csv"

# Resultado esperado:
# {"lote_id":"uuid-aqui","status":"PENDENTE","mensagem":"..."}
```

### 4. Monitorar worker

```bash
# Ver logs do worker processando
docker logs fastmission-worker -f

# Deve aparecer:
# Task processar_lote_task received
# Processando item 1/5
# Task succeeded
```

### 5. Verificar no banco

```bash
# Ver lotes
docker exec fastmission-postgres psql -U fastmission -d cadastral_db -c "SELECT * FROM lotes;"

# Ver itens processados
docker exec fastmission-postgres psql -U fastmission -d cadastral_db -c "SELECT descricao, ncm_original, status_validacao FROM itens_cadastrais LIMIT 5;"
```

---

## ✅ Se tudo funcionou local, commitar:

```bash
# Adicionar arquivos novos
git add docker-compose.prod.yml backend/.dockerignore .env.example .gitignore test_upload.csv backend/app/main.py

# Commit
git commit -m "feat: Add production configuration for Easypanel deploy"

# Push
git push origin main
```

---

## 🌐 Deploy no Easypanel

### 1. Criar App no Easypanel

- **New App** → **From Source**
- **Repository:** `https://github.com/ggasparott/FastMission`
- **Branch:** `main`
- **Docker Compose File:** `docker-compose.prod.yml` ⚠️

### 2. Configurar Variáveis de Ambiente

No painel do Easypanel, adicionar:

```
POSTGRES_USER=fastmission
POSTGRES_PASSWORD=SuaSenhaSegura123!XYZ
POSTGRES_DB=cadastral_db
```

**⚠️ IMPORTANTE:** Use senha forte! Gerar com:
```bash
openssl rand -base64 32
```

### 3. Configurar Domínio (opcional)

- **Domain:** `api.seudominio.com.br`
- **Enable SSL:** ✅ (Let's Encrypt automático)

### 4. Deploy

Clicar em **Deploy** e aguardar build.

### 5. Aplicar Migrations no Easypanel

Após deploy bem-sucedido:

```bash
# SSH no servidor OU usar terminal do Easypanel
docker exec <container-backend> alembic upgrade head
```

### 6. Verificar

```bash
curl https://api.seudominio.com.br/health
```

---

## 🔍 Troubleshooting

### Backend não sobe
```bash
docker logs fastmission-backend
```

### Worker não processa
```bash
docker logs fastmission-worker
docker exec fastmission-redis redis-cli LLEN celery
```

### Erro de conexão com Postgres
```bash
docker exec fastmission-backend python -c "from app.database import engine; engine.connect()"
```

---

## 📊 Diferenças Dev vs Prod

| Aspecto | Dev | Prod |
|---------|-----|------|
| Reload | `--reload` | `--workers 2` |
| Volumes | Monta código | Não monta |
| Docs | `/docs` habilitado | Desabilitado |
| Restart | `unless-stopped` | `always` |
| Senhas | Hardcoded | Env vars |

---

## 🔄 Auto-Deploy (opcional)

Configure no Easypanel:
- **Auto-deploy on push:** ✅ Enabled

Agora toda vez que você der `git push`, o Easypanel automaticamente rebuilda! 🚀

---

## 📝 Próximos Passos

1. ✅ Testar local
2. ✅ Commitar configs de produção
3. ✅ Deploy no Easypanel
4. ⬜ Criar frontend React
5. ⬜ Integrar LLM real (OpenAI/Claude)
6. ⬜ Adicionar autenticação

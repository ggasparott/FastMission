# Plano: MVP Saneamento Cadastral - Teste de Conceito

## Visão Geral do MVP

**Objetivo:** Testar a viabilidade de usar IA para auditar classificações fiscais (NCM) de produtos no contexto da nova Reforma Tributária brasileira (IBS/CBS).

**Escopo Reduzido:** MVP focado apenas em provar que a IA consegue detectar NCMs incorretos com precisão aceitável. Não é um SaaS completo - é um protótipo funcional para validar a hipótese.

**Fluxo Simplificado:**
1. Upload CSV → API salva e retorna "202 Accepted"
2. Worker Celery pega tarefa → Chama script de IA → Atualiza banco
3. Frontend mostra status em tempo real e lista divergências

---

## Stack Tecnológica (Mínima Viável)

### Backend (Python)
- **Framework:** FastAPI (Async)
- **Task Queue:** Celery + Redis (apenas para processamento IA)
- **Database:** PostgreSQL + SQLAlchemy
- **IA:** OpenAI/OpenInterpreter (via script externo)
- **Python:** 3.11+

### Frontend (React)
- **Build Tool:** Vite
- **Styling:** TailwindCSS
- **Icons:** Lucide-React
- **State:** React Hooks + Axios

---

## Estrutura de Pastas

```
FastMission/
├── backend/
│   ├── app/
│   │   ├── main.py           # Entry point FastAPI
│   │   ├── database.py       # Conexão SQLAlchemy
│   │   ├── models.py         # Modelos ORM
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── routes.py         # Endpoints API
│   │   └── tasks.py          # Tarefas Celery
│   ├── skills/
│   │   └── validate_ncm.py   # Script IA validação
│   ├── alembic/              # Migrations
│   ├── requirements.txt
│   └── celeryconfig.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── UploadCSV.jsx
│   │   │   ├── BatchList.jsx
│   │   │   └── ItemTable.jsx
│   │   └── api/
│   │       └── client.js
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── .env.example
```

---

## 1. Banco de Dados (PostgreSQL + SQLAlchemy)

### Pseudocódigo: models.py

```python
# Dois modelos principais para o MVP

class Lote:
    """Representa um batch de upload CSV"""
    id: UUID (chave primária)
    arquivo_nome: String (ex: "produtos_2024.csv")
    status: Enum("PENDENTE", "PROCESSANDO", "CONCLUIDO", "ERRO")
    total_itens: Integer (quantos produtos no CSV)
    data_upload: DateTime (timestamp do upload)
    relacionamento: List[ItemCadastral] (1 para muitos)

class ItemCadastral:
    """Cada linha do CSV é um ItemCadastral"""
    id: UUID (chave primária)
    lote_id: UUID (foreign key para Lote)
    
    # Dados originais do CSV
    descricao: String (ex: "CHOCOLATE AO LEITE 200G")
    ncm_original: String (ex: "1806.31.00")  # ⚠️ STRING, não INT!
    
    # Resultado da IA
    ncm_sugerido: String (nullable, ex: "1704.90.00")
    status_validacao: Enum("PENDENTE", "VALIDO", "DIVERGENTE")
    motivo_divergencia: Text (explicação da IA)
    confianca_ai: Float (0-100, score de certeza)
    
    data_processamento: DateTime (quando a IA analisou)
```

**📖 Ensinamento:**
- NCM é **sempre String** porque "0102.31.00" começa com zero (se for INT perde o formato)
- Use `Enum` para status (evita typos como "CONCLUIDO" vs "CONCLUÍDO")
- `motivo_divergencia` armazena a explicação da IA em texto livre

---

### Pseudocódigo: schemas.py (Pydantic)

```python
# Validação de dados de entrada/saída da API

class LoteResponse:
    """O que a API retorna ao fazer upload"""
    id: UUID
    status: str
    total_itens: int
    arquivo_nome: str

class ItemCadastralResponse:
    """Cada item na listagem"""
    id: UUID
    descricao: str
    ncm_original: str
    ncm_sugerido: Optional[str]  # Pode ser None se ainda não processou
    status_validacao: str
    motivo_divergencia: Optional[str]
    confianca_ai: Optional[float]
```

**📖 Ensinamento:**
- Pydantic valida automaticamente os tipos na entrada/saída da API
- `Optional[str]` = pode ser None (ainda não processado pela IA)
- Campos calculados podem ser adicionados (ex: cor para frontend)

---

## 2. API Routes (FastAPI)

### Pseudocódigo: routes.py

```python
# ===== ENDPOINT 1: Upload CSV =====

@app.post("/upload", status_code=202)
async def upload_csv(file: UploadFile):
    """
    ⚠️ REGRA DE OURO: NUNCA processa aqui! Apenas salva e agenda.
    """
    
    # Passo 1: Validar arquivo
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Apenas CSV aceito")
    
    # Passo 2: Ler CSV e parsear
    conteudo = await file.read()
    linhas = parsear_csv(conteudo)  # Tenta UTF-8, depois Latin-1
    
    # Passo 3: Criar Lote no banco
    lote = Lote(
        arquivo_nome=file.filename,
        status="PENDENTE",
        total_itens=len(linhas)
    )
    db.add(lote)
    db.commit()
    
    # Passo 4: Criar todos os itens (bulk insert)
    for linha in linhas:
        item = ItemCadastral(
            lote_id=lote.id,
            descricao=linha['descricao'],
            ncm_original=linha['ncm'],  # String!
            status_validacao="PENDENTE"
        )
        db.add(item)
    db.commit()
    
    # Passo 5: Agendar processamento (enviar para Redis via Celery)
    processar_lote_task.delay(lote.id)  # ⚡ Async magic
    
    # Retornar imediatamente (202 = "recebi, processando em background")
    return {
        "lote_id": lote.id, 
        "status": "PENDENTE", 
        "mensagem": "Processando em background"
    }


# ===== ENDPOINT 2: Checar Status =====

@app.get("/lotes/{lote_id}/status")
async def get_status(lote_id: UUID):
    """
    Frontend chama isso a cada 3 segundos (polling)
    """
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    
    if not lote:
        raise HTTPException(404, "Lote não encontrado")
    
    # Calcular progresso
    itens_processados = db.query(ItemCadastral).filter(
        ItemCadastral.lote_id == lote_id,
        ItemCadastral.status_validacao != "PENDENTE"
    ).count()
    
    progresso = (itens_processados / lote.total_itens) * 100
    
    return {
        "status": lote.status,
        "progresso": progresso,
        "total_itens": lote.total_itens,
        "itens_processados": itens_processados
    }


# ===== ENDPOINT 3: Listar Itens com Divergências =====

@app.get("/lotes/{lote_id}/itens")
async def listar_itens(lote_id: UUID, apenas_divergentes: bool = False):
    """
    Lista os itens, com filtro opcional para mostrar só problemas
    """
    query = db.query(ItemCadastral).filter(ItemCadastral.lote_id == lote_id)
    
    if apenas_divergentes:
        query = query.filter(ItemCadastral.status_validacao == "DIVERGENTE")
    
    itens = query.all()
    
    return [ItemCadastralResponse.from_orm(item) for item in itens]
```

**📖 Ensinamentos:**
1. **202 Accepted**: Código HTTP que significa "recebi, mas ainda estou processando"
2. **Polling**: Frontend fica perguntando "terminou?" a cada 3 segundos
3. **Bulk Insert**: Crie todos os itens de uma vez (melhor performance)
4. **Query Filtering**: Use SQLAlchemy filters para buscar no banco

---

## 3. Celery Worker (Processamento Assíncrono)

### Pseudocódigo: tasks.py

```python
from celery import Celery
import subprocess
import json

celery_app = Celery('fastmission', broker='redis://localhost:6379/0')

@celery_app.task
def processar_lote_task(lote_id: str):
    """
    Esta função roda num processo separado (worker).
    É chamada pela fila Redis quando você faz .delay()
    """
    
    try:
        # Marcar lote como em processamento
        lote = db.query(Lote).filter(Lote.id == lote_id).first()
        lote.status = "PROCESSANDO"
        db.commit()
        
        # Buscar todos os itens pendentes
        itens = db.query(ItemCadastral).filter(
            ItemCadastral.lote_id == lote_id,
            ItemCadastral.status_validacao == "PENDENTE"
        ).all()
        
        # Processar cada item com IA
        for item in itens:
            # ⚠️ CHAVE: Chame script externo, NÃO código inline!
            resultado = chamar_ai_script(item.descricao, item.ncm_original)
            
            # Atualizar item com resultado
            item.ncm_sugerido = resultado['ncm_sugerido']
            item.status_validacao = resultado['status']
            item.motivo_divergencia = resultado['explicacao']
            item.confianca_ai = resultado['confianca']
            db.commit()
        
        # Marcar lote como concluído
        lote.status = "CONCLUIDO"
        db.commit()
        
    except Exception as e:
        # ⚠️ CRÍTICO: Se der erro, não crashar o worker!
        lote.status = "ERRO"
        db.commit()
        print(f"Erro ao processar lote {lote_id}: {e}")


def chamar_ai_script(descricao: str, ncm: str) -> dict:
    """
    Chama o script Python em skills/ via subprocess
    """
    # Preparar dados para o script
    entrada = json.dumps({"descricao": descricao, "ncm": ncm})
    
    # Executar script
    resultado = subprocess.run(
        ["python", "skills/validate_ncm.py"],
        input=entrada,
        capture_output=True,
        text=True
    )
    
    # Parsear resposta JSON
    return json.loads(resultado.stdout)
```

**📖 Ensinamentos:**
1. **Celery Worker**: Processo separado que fica esperando tarefas na fila Redis
2. **Try/Except Crucial**: Se não colocar, um erro mata o worker inteiro
3. **Subprocess**: Chama script externo (mantém lógica de IA separada da API)
4. **Status Tracking**: Atualiza DB em cada etapa (PENDENTE → PROCESSANDO → CONCLUIDO)

---

## 4. Script de IA (skills/validate_ncm.py)

### Pseudocódigo: validate_ncm.py

```python
import sys
import json
# from openai import OpenAI  # ou qualquer LLM que você escolher

def validar_ncm(descricao: str, ncm_original: str) -> dict:
    """
    Lógica de IA/Merceologia aqui
    """
    
    # Prompt para LLM (exemplo simplificado - você vai refinar isso)
    prompt = f"""
    Você é um especialista em Merceologia (ciência de classificação de mercadorias) 
    e conhece profundamente a tabela NCM brasileira.
    
    Analise se o produto está classificado corretamente:
    - Descrição do Produto: {descricao}
    - NCM Atual: {ncm_original}
    
    Tarefas:
    1. O NCM está correto para essa descrição?
    2. Se NÃO, qual NCM deveria ser usado?
    3. Explique o motivo baseado em Merceologia (composição, uso, matéria-prima).
    
    Retorne APENAS JSON válido (sem markdown):
    {{
        "correto": true/false,
        "ncm_sugerido": "XXXX.XX.XX",
        "explicacao": "texto detalhado",
        "confianca": 0-100
    }}
    """
    
    # Chamar LLM (OpenAI, Claude, etc)
    # resposta_ai = chamar_llm(prompt)
    
    # Para MVP, você pode mockar respostas primeiro:
    resposta_ai = {
        "correto": False,
        "ncm_sugerido": "1806.32.00",
        "explicacao": "Produto descrito como 'chocolate' mas NCM aponta para 'wafer'",
        "confianca": 85
    }
    
    # Processar resposta
    if resposta_ai['correto']:
        return {
            "ncm_sugerido": ncm_original,  # Manter o mesmo
            "status": "VALIDO",
            "explicacao": "Classificação correta segundo Merceologia",
            "confianca": resposta_ai['confianca']
        }
    else:
        return {
            "ncm_sugerido": resposta_ai['ncm_sugerido'],
            "status": "DIVERGENTE",
            "explicacao": resposta_ai['explicacao'],
            "confianca": resposta_ai['confianca']
        }


# Entry point para subprocess
if __name__ == "__main__":
    # Ler JSON do stdin
    entrada = json.loads(sys.stdin.read())
    
    # Processar
    resultado = validar_ncm(entrada['descricao'], entrada['ncm'])
    
    # Retornar JSON no stdout
    print(json.dumps(resultado))
```

**📖 Ensinamentos:**
1. **Script Isolado**: Roda independente do FastAPI (facilita debug e testes)
2. **stdin/stdout**: Comunicação via JSON (padrão Unix/subprocess)
3. **Prompt Engineering**: Ensine a IA sobre Merceologia no prompt
4. **Confiança**: Score de 0-100 ajuda a filtrar resultados duvidosos no MVP

---

## 5. Frontend - Upload Component

### Pseudocódigo: UploadCSV.jsx

```jsx
import { useState } from 'react';
import { Upload } from 'lucide-react';
import axios from 'axios';

function UploadCSV() {
  const [arquivo, setArquivo] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const [loteId, setLoteId] = useState(null);

  const handleUpload = async () => {
    if (!arquivo) return;

    setCarregando(true);

    // Criar FormData para enviar arquivo
    const formData = new FormData();
    formData.append('file', arquivo);

    try {
      // Chamar API (202 Accepted)
      const response = await axios.post('http://localhost:8000/upload', formData);
      
      // Salvar ID do lote para polling
      setLoteId(response.data.lote_id);
      
      alert('Upload iniciado! Processando em background...');
    } catch (erro) {
      alert('Erro no upload: ' + erro.message);
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4">Upload de Cadastro (CSV)</h2>
      
      <input
        type="file"
        accept=".csv"
        onChange={(e) => setArquivo(e.target.files[0])}
        className="mb-4"
      />
      
      <button
        onClick={handleUpload}
        disabled={!arquivo || carregando}
        className="bg-blue-600 text-white px-4 py-2 rounded flex items-center gap-2 disabled:opacity-50"
      >
        <Upload size={20} />
        {carregando ? 'Enviando...' : 'Fazer Upload'}
      </button>

      {loteId && (
        <p className="mt-4 text-green-600">
          Lote criado: {loteId}
        </p>
      )}
    </div>
  );
}
```

**📖 Ensinamentos:**
1. **FormData**: Necessário para enviar arquivos via HTTP
2. **useState**: Gerencia estado local (arquivo, loading, loteId)
3. **TailwindCSS**: Classes utilitárias (bg-white, p-6, rounded-lg)
4. **Lucide Icons**: Import direto de componentes (`<Upload />`)

---

### Pseudocódigo: BatchList.jsx (Polling de Status)

```jsx
import { useEffect, useState } from 'react';
import axios from 'axios';

function BatchList({ loteId }) {
  const [status, setStatus] = useState(null);
  const [polling, setPolling] = useState(true);

  useEffect(() => {
    if (!loteId || !polling) return;

    // Função de polling
    const verificarStatus = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/lotes/${loteId}/status`);
        setStatus(response.data);

        // Parar de fazer polling se concluiu ou deu erro
        if (response.data.status === 'CONCLUIDO' || response.data.status === 'ERRO') {
          setPolling(false);
        }
      } catch (erro) {
        console.error('Erro ao checar status:', erro);
      }
    };

    // Chamar imediatamente
    verificarStatus();

    // Configurar intervalo de 3 segundos
    const intervalo = setInterval(verificarStatus, 3000);

    // Cleanup: parar intervalo quando componente desmontar
    return () => clearInterval(intervalo);
  }, [loteId, polling]);

  if (!status) return <p>Carregando...</p>;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-bold">Status do Lote</h3>
      
      <div className="mt-4">
        <p>Status: <span className="font-semibold">{status.status}</span></p>
        <p>Progresso: {status.progresso.toFixed(1)}%</p>
        
        {/* Barra de progresso */}
        <div className="w-full bg-gray-200 rounded h-4 mt-2">
          <div 
            className="bg-blue-600 h-4 rounded transition-all duration-300"
            style={{ width: `${status.progresso}%` }}
          />
        </div>
        
        <p className="text-sm text-gray-600 mt-2">
          {status.itens_processados} de {status.total_itens} itens processados
        </p>
      </div>
    </div>
  );
}
```

**📖 Ensinamentos:**
1. **useEffect**: Executa código quando componente monta
2. **setInterval**: Chama função a cada X segundos (polling pattern)
3. **Cleanup**: `return () => clearInterval()` evita memory leaks
4. **Conditional Render**: `if (!status)` mostra loading state

---

### Pseudocódigo: ItemTable.jsx (Lista de Divergências)

```jsx
import { CheckCircle, AlertTriangle } from 'lucide-react';

function ItemTable({ loteId }) {
  const [itens, setItens] = useState([]);
  const [filtro, setFiltro] = useState(false); // Mostrar só divergências?

  useEffect(() => {
    const buscarItens = async () => {
      const url = `http://localhost:8000/lotes/${loteId}/itens?apenas_divergentes=${filtro}`;
      const response = await axios.get(url);
      setItens(response.data);
    };

    buscarItens();
  }, [loteId, filtro]);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold">Itens Cadastrais</h3>
        
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={filtro}
            onChange={(e) => setFiltro(e.target.checked)}
          />
          Mostrar apenas divergências
        </label>
      </div>

      <table className="w-full">
        <thead className="bg-gray-100">
          <tr>
            <th className="p-2 text-left">Descrição</th>
            <th className="p-2 text-left">NCM Original</th>
            <th className="p-2 text-left">NCM Sugerido</th>
            <th className="p-2 text-left">Status</th>
            <th className="p-2 text-left">Motivo</th>
            <th className="p-2 text-left">Confiança</th>
          </tr>
        </thead>
        <tbody>
          {itens.map(item => (
            <tr 
              key={item.id}
              className={
                item.status_validacao === 'DIVERGENTE' 
                  ? 'bg-red-50' 
                  : item.status_validacao === 'VALIDO'
                  ? 'bg-green-50'
                  : 'bg-gray-50'
              }
            >
              <td className="p-2">{item.descricao}</td>
              <td className="p-2 font-mono text-sm">{item.ncm_original}</td>
              <td className="p-2 font-mono text-sm">{item.ncm_sugerido || '-'}</td>
              <td className="p-2">
                {item.status_validacao === 'VALIDO' ? (
                  <span className="flex items-center gap-1 text-green-600">
                    <CheckCircle size={16} />
                    Válido
                  </span>
                ) : item.status_validacao === 'DIVERGENTE' ? (
                  <span className="flex items-center gap-1 text-red-600">
                    <AlertTriangle size={16} />
                    Divergente
                  </span>
                ) : (
                  <span className="text-gray-500">Pendente</span>
                )}
              </td>
              <td className="p-2 text-sm text-gray-700">
                {item.motivo_divergencia || '-'}
              </td>
              <td className="p-2 text-sm">
                {item.confianca_ai ? `${item.confianca_ai}%` : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**📖 Ensinamentos:**
1. **Conditional Styling**: `bg-red-50` se divergente, `bg-green-50` se válido
2. **Icons**: `<CheckCircle />` verde, `<AlertTriangle />` vermelho
3. **font-mono**: NCM codes ficam mais legíveis com fonte monoespaçada
4. **Query Params**: `?apenas_divergentes=true` filtra no backend

---

## 6. Infrastructure - Docker Compose

### Pseudocódigo: docker-compose.yml

```yaml
version: '3.8'

services:
  # Banco PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: fastmission
      POSTGRES_PASSWORD: senha123
      POSTGRES_DB: cadastral_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis para Celery
  redis:
    image: redis:7
    ports:
      - "6379:6379"

  # Backend FastAPI
  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://fastmission:senha123@postgres:5432/cadastral_db
      REDIS_URL: redis://redis:6379/0

  # Celery Worker (processamento async)
  worker:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://fastmission:senha123@postgres:5432/cadastral_db
      REDIS_URL: redis://redis:6379/0

  # Frontend React (dev mode)
  frontend:
    build: ./frontend
    command: npm run dev -- --host
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
```

**📖 Ensinamentos:**
1. **depends_on**: Define ordem de inicialização dos serviços
2. **volumes**: Persiste dados do Postgres entre restarts
3. **environment**: Variáveis de ambiente (conexões de banco/redis)
4. **Worker separado**: Serviço independente para processar fila Celery

---

## 7. Teste do MVP - CSV de Exemplo

### Estrutura do CSV de Teste

```csv
descricao,ncm
CHOCOLATE AO LEITE 200G,1806.31.00
WAFER RECHEADO CHOCOLATE 100G,1905.90.00
PARAFUSO SEXTAVADO AÇO INOX,7318.15.00
SABONETE GLICERINA NATURAL,3401.11.90
NOTEBOOK CORE I5 8GB RAM,8471.30.12
TECLADO MECÂNICO RGB USB,8471.60.53
REFRIGERANTE COLA 2L PET,2202.10.00
CERVEJA PILSEN 350ML LATA,2203.00.00
FARINHA DE TRIGO TIPO 1 KG,1101.00.10
ÓLEO DE SOJA REFINADO 900ML,1507.90.11
```

### Como Testar Manualmente

```bash
# 1. Subir infraestrutura
docker-compose up -d

# 2. Aplicar migrations (primeira vez)
docker-compose exec backend alembic upgrade head

# 3. Acessar frontend
# Abrir navegador em: http://localhost:5173

# 4. Fazer upload do CSV de teste

# 5. Verificar logs do worker em tempo real
docker-compose logs -f worker

# 6. Checar banco de dados diretamente (debug)
docker-compose exec postgres psql -U fastmission -d cadastral_db
# Dentro do psql:
SELECT id, descricao, ncm_original, status_validacao FROM item_cadastral LIMIT 10;

# 7. Testar API diretamente (sem frontend)
curl -X POST http://localhost:8000/upload -F "file=@produtos.csv"
```

---

## Decisões Arquiteturais do MVP

### 1. Por que Celery + Redis e não processar direto?
**Problema:** CSV com 1,000 produtos = 1,000 chamadas de IA = 10+ minutos  
**Solução:** 
- Usuário faz upload → API responde em 100ms com "202 Accepted"
- Worker processa em background
- Frontend faz polling para atualizar progresso

**Alternativas descartadas:**
- ❌ Processar no endpoint (timeout HTTP após 30s)
- ❌ WebSockets (complexidade desnecessária para MVP)

### 2. Por que subprocess para chamar IA?
**Vantagens:**
- Isola lógica de LLM (fácil trocar OpenAI → Claude → Ollama)
- Script pode ser testado standalone: `python skills/validate_ncm.py < test.json`
- Se IA crashar, não derruba FastAPI
- Facilita debugar prompts sem subir toda infraestrutura

**Alternativas descartadas:**
- ❌ Código inline em tasks.py (dificulta testes e manutenção)
- ❌ API externa separada (overhead desnecessário para MVP)

### 3. Por que NCM como String e não Integer?
**Problema:** NCM "0102.31.00" vira 102 se for Integer  
**Regulação:** Receita Federal exige exatamente 8 dígitos com pontos  
**Solução:** String preserva zeros à esquerda e formatação

### 4. Por que PostgreSQL e não SQLite?
**MVP pode crescer:** PostgreSQL já prepara pra produção  
**Concorrência:** Celery workers simultâneos precisam de DB robusto  
**Simplicidade:** Docker Compose torna setup praticamente igual

---

## Próximos Passos Após MVP

### Validação de Hipótese
1. **Precisão da IA:** % de acertos vs base conhecida
2. **Velocidade:** Tempo médio por item
3. **Custo:** $ de API de IA por 1000 produtos
4. **Usabilidade:** Usuários conseguem usar sem treinamento?

### Melhorias Futuras (se MVP validar)
- [ ] Autenticação de usuários
- [ ] Multi-tenancy (várias empresas)
- [ ] Exportar relatório em Excel
- [ ] Dashboard com métricas (% divergências por categoria)
- [ ] Histórico de auditorias
- [ ] Integração com ERPs brasileiros (TOTVS, SAP)

---

## Resumo de Comandos Úteis

```bash
# Iniciar tudo
docker-compose up -d

# Ver logs de um serviço específico
docker-compose logs -f worker
docker-compose logs -f backend

# Parar tudo
docker-compose down

# Resetar banco (CUIDADO: apaga dados)
docker-compose down -v
docker-compose up -d

# Acessar shell do container
docker-compose exec backend bash
docker-compose exec postgres psql -U fastmission -d cadastral_db

# Rodar migration
docker-compose exec backend alembic revision --autogenerate -m "create tables"
docker-compose exec backend alembic upgrade head

# Instalar nova dependência Python
docker-compose exec backend pip install nome-pacote
# Depois atualizar requirements.txt
docker-compose exec backend pip freeze > requirements.txt
```

---

## Checklist de Implementação

### Backend
- [ ] Criar estrutura de pastas
- [ ] Configurar SQLAlchemy (database.py, models.py)
- [ ] Criar schemas Pydantic (schemas.py)
- [ ] Implementar endpoints FastAPI (routes.py)
- [ ] Configurar Celery + Redis (tasks.py, celeryconfig.py)
- [ ] Criar script de IA (skills/validate_ncm.py)
- [ ] Setup migrations Alembic
- [ ] Criar requirements.txt

### Frontend
- [ ] Criar projeto Vite + React
- [ ] Configurar TailwindCSS
- [ ] Instalar Lucide-React
- [ ] Criar componente UploadCSV
- [ ] Criar componente BatchList (polling)
- [ ] Criar componente ItemTable
- [ ] Configurar Axios client

### Infrastructure
- [ ] Criar docker-compose.yml
- [ ] Criar Dockerfiles (backend e frontend)
- [ ] Criar .env.example
- [ ] Testar docker-compose up

### Testes
- [ ] CSV de exemplo com casos conhecidos
- [ ] Testar upload via frontend
- [ ] Verificar processamento no worker
- [ ] Validar resultados no banco
- [ ] Testar filtros e polling

---

**Boa implementação! 🚀**

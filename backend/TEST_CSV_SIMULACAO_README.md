# 📋 Simulador de Validação - 20 Itens de Teste

**Arquivo:** `test_produtos_simulacao_20itens.csv`  
**Data criação:** 2026-04-09  
**Propósito:** Validar pipeline completo: Upload → Agent IA → Análise → Frontend

---

## 📊 Resumo dos Itens

| # | Categoria | Descrição | NCM | CEST | Qtd | Valor Unit | Caso de Teste |
|---|---|---|---|---|---|---|---|
| 1 | Vestiário | Camiseta 100% Algodão | 61045090 | 16000 | 150 | R$ 29,90 | ✓ Válido com benefício? |
| 2 | Vestiário | Calça Jeans Masculina | 62034200 | 16001 | 80 | R$ 89,90 | ✓ Básico válido |
| 3 | Vestiário | Jaqueta Couro Sintético | 62063000 | - | 45 | R$ 199,90 | ⚠ Sem CEST |
| 4 | Vestiário | Vestido Feminino Social | 62033100 | 16002 | 30 | R$ 149,90 | ✓ Válido |
| 5 | Vestiário | Meia Soquete Algodão | 61159000 | 16010 | 500 | R$ 8,90 | ✓ Alto volume |
| 6 | Alimentos | Leite Integral 1L | 04012100 | - | 200 | R$ 4,50 | 💰 Cesta básica? |
| 7 | Alimentos | Pão Francês Tradicional | 19053000 | - | 800 | R$ 0,90 | 💰 Alíquota 0% |
| 8 | Alimentos | Arroz Branco Tipo 1 | 10061000 | - | 500 | R$ 3,90 | 💰 Cesta básica |
| 9 | Alimentos | Feijão Carioca Premium | 07133000 | - | 400 | R$ 7,50 | 💰 Cesta básica |
| 10 | Alimentos | Maçã Fuji Importada | 08081090 | - | 300 | R$ 5,90 | 💰 Importado |
| 11 | Pharma | Medicamento Dipirona | 30049010 | - | 100 | R$ 2,50 | 💊 Medicamento |
| 12 | Pharma | Vitamina C 1000mg | 21069090 | - | 150 | R$ 12,90 | 💊 Suplemento |
| 13 | Cosmética | Shampoo Neutro 250ml | 33041000 | - | 200 | R$ 15,90 | ✓ Normal |
| 14 | Cosmética | Desodorante Antitransp | 33072090 | - | 180 | R$ 18,90 | ✓ Normal |
| 15 | Eletrônicos | Fone Bluetooth | 85183090 | 17000 | 50 | R$ 199,90 | 🔌 Tech + CEST |
| 16 | Eletrônicos | Carregador USB-C | 85443099 | 17001 | 120 | R$ 89,90 | 🔌 Acessório |
| 17 | Eletrônicos | Cabo HDMI 2m | 85447090 | - | 200 | R$ 35,90 | 🔌 Commodity |
| 18 | Eletrônicos | Teclado Mecânico RGB | 84716060 | - | 60 | R$ 349,90 | 🔌 Premium |
| 19 | Periféricos | Mousepad Grande | 95069090 | - | 100 | R$ 45,90 | ✓ Acessório |
| 20 | Periféricos | Webcam Full HD 1080p | 90281090 | 18000 | 35 | R$ 249,90 | 🔌 Tech + CEST |

---

## 🎯 Casos de Teste Cobertos

### **1. Classificação Válida (5 itens)**
- Itens onde NCM atual está correto
- Esperado: **Status = VALIDO**, sem divergência
- Exemplos: Calça (62034200), Vestido (62033100), Shampoo (33041000)

### **2. Benefícios Fiscais (6 itens)**
- Alimentos de cesta básica (NCM 07, 10, 19)
- Medicamentos (NCM 30, 21)
- Esperado: **possui_beneficio_fiscal = SIM**, alíquota reduzida
- Produtos: Leite, Pão, Arroz, Feijão, Maçã, Dipirona, Vitamina C

### **3. Eletrônicos com CEST (5 itens)**
- Produtos que exigem CEST obrigatório
- Esperado: CEST validado e presente na resposta
- Exemplos: Fone (17000), Carregador (17001), Webcam (18000)

### **4. Vestiário com Variação (5 itens)**
- Diferentes tipos de roupa
- Esperado: Confirmação de classificação ou ajuste de regime
- Teste de ST (Substituição Tributária)?

---

## 💰 Cálculos Esperados

### **Exemplo Item 1: Camiseta**
```
NCM: 61045090 (Vestiário - Algodão)
CEST: 16000 (Substituição Tributária)
Quantidade: 150
Valor Unitário: R$ 29,90
Base de Cálculo: 150 × 29,90 = R$ 4.485,00

Carga Atual (SIMPLES):
- ICMS: ~7% = R$ 313,95
- PIS: 0% = R$ 0,00
- COFINS: 0% = R$ 0,00
- Subtotal: R$ 313,95

Carga Reforma (IBS/CBS):
- Estimado: ~27% = R$ 1.210,95
- Diferença: -R$ 897 (pode aumentar com IBS)
```

### **Exemplo Item 7: Pão Francês**
```
NCM: 19053000 (Pão e similar)
Quantidade: 800
Valor Unitário: R$ 0,90
Base: 800 × 0,90 = R$ 720,00

Carga Atual:
- ICMS: 0% (cesta básica)
- Total: R$ 0,00

Carga Reforma:
- IBS: 0% (mantém cesta básica)
- Total: R$ 0,00

Esperado: Benefício confirmado, economia = 0
```

---

## 📈 Distribuição de Características

```
Por Tipo de Produto:
├─ Vestiário (5): 61045090, 62034200, 62063000, 62033100, 61159000
├─ Alimentos (5): 04012100, 19053000, 10061000, 07133000, 08081090
├─ Farmacêutico (2): 30049010, 21069090
├─ Cosmética (2): 33041000, 33072090
└─ Eletrônico (6): 85183090, 85443099, 85447090, 84716060, 95069090, 90281090

Por CEST:
├─ Com CEST (8): 16000, 16001, 16002, 16010, 17000, 17001, 18000
└─ Sem CEST (12): resto

Por Volume:
├─ Alto (200+): 5 itens (Meia, Leite, Pão, Arroz, Cabo)
├─ Médio (100-200): 7 itens
└─ Baixo (<100): 8 itens

Por Valor Unit:
├─ Barato (<R$20): 9 itens (teste de quantidade compensar)
├─ Médio (R$20-R$100): 6 itens
└─ Caro (>R$100): 5 itens (teste com economia % alta)
```

---

## 🧪 Roteiro de Testes

### **Passo 1: Upload**
```bash
# URL: http://localhost:5173
# Preencher formulário:
- Regime Empresa: LUCRO_REAL (ou SIMPLES para teste)
- UF Origem: SP
- UF Destino: RJ
- CNAE Principal: 1413800 (Fabricação de peças de vestuário)
# Selecionar: test_produtos_simulacao_20itens.csv
# Clicar: "Iniciar Análise"
```

### **Passo 2: Validação Backend**
```bash
# Esperar 30-60s para processamento
# Observar console Celery:
# [Celery] Processando 20 itens do lote ...
# [Celery] Item 1/20 processado: VALIDO
# [Celery] Item 2/20 processado: VALIDO
# ...
# [Celery] Lote concluído com sucesso!
```

### **Passo 3: Visualização Frontend**
```
Esperado ver:
- Card "Total de Itens": 20
- Card "Válidos": ~15
- Card "Divergentes": ~0
- Card "Com Benefícios": ~6
- Progresso: 100%

Abas:
- Todos (20)
- ✓ Válidos (~15)
- ⚠ Divergentes (~0-3)
- 💰 Benefícios (~6)
```

### **Passo 4: Análise de Resultados**

```
Verificar por coluna:

Status (deve mostrar badges):
├─ ✓ VALIDO (maioria)
├─ ⚠ DIVERGENTE (alguns eletrônicos?)
└─ Color coding correto

NCM (deve mostrar original → sugerido se diferente):
├─ Camiseta (61045090): sem mudança
├─ Carregador (85443099): pode sugerir ajuste?
└─ Alimentos: verificar se mantém NCM

Confiança (barra com cores):
├─ Verde (70-100%): itens bem classificados
├─ Amarelo (50-70%): incerto
└─ Vermelho (<50%): muito incerto

Carga Atual vs Reforma:
├─ Vestiário: ~10-20% antes, ~27% depois
├─ Alimentos: 0% (cesta básica) mantém
└─ Eletrônico: ~15-25% antes, ~27% depois

Benefício:
├─ Alimentos: ✓ Confirmados
├─ Medicamentos: ✓ Confirmados
└─ Resto: - Nenhum (esperado)
```

### **Passo 5: Export CSV**
```bash
# Clicar "Exportar CSV"
# Arquivo baixado: lote_<id>_analise.csv
# Abrir em Excel/Google Sheets
# Verificar:
- 20 linhas de dados
- Colunas: Descrição, NCM, CEST, Status, Confiança, Regime, etc.
- Sem caracteres estranhos
- Valores numéricos alinhados à direita
```

---

## 🔍 O que Observar em Detalhes

### **1. Cálculo de Economia**
Para item 1 (Camiseta):
- Base: R$ 4.485,00
- Carga Atual: ~7% = R$ 313,95
- Carga Reforma: ~27% = R$ 1.210,95
- Diferença: **-R$ 897,00** (AUMENTA imposto, não economiza)

Para item 7 (Pão - cesta básica):
- Base: R$ 720,00
- Carga Atual: 0%
- Carga Reforma: 0% (mantém benefício)
- Diferença: **R$ 0,00** (sem mudança)

### **2. Confiança do Agente**
- Esperado: 85-95% para produtos simples
- Pode cair para 60-75% para casos ambíguos
- Verificar se barra de cor acompanha %

### **3. Divergências**
- Alguns eletrônicos podem ter NCM sugerido diferente
- Verificar motivo em tooltip de justificativa
- CEST obrigatório pode ser indicado

### **4. Dashboard**
```
Stats esperadas:
- Total Itens: 20
- Válidos: ~15-18
- Divergentes: ~0-3
- Com Benefícios: ~6
- Economia Total: Negativa (reforma aumenta imposto em ST)
```

---

## 📝 Checklist de Validação

- [ ] Upload aceita arquivo CSV
- [ ] Backend aceita 20 linhas sem erro
- [ ] Celery processa todos os 20 itens
- [ ] Frontend exibe 20 itens na tabela
- [ ] Abas mostram filtros corretos
- [ ] Status badges aparecem com cores corretas
- [ ] Confiança exibe como barra + %
- [ ] NCM divergências mostram seta
- [ ] Tooltips funcionam ao passar mouse
- [ ] Export CSV baixa arquivo válido
- [ ] Cálculos de economia fazem sentido
- [ ] Benefícios fiscais detectados corretamente
- [ ] Nenhum erro no console (frontend/backend)

---

## 🚀 Comando para Testar Localmente

```bash
# Se quiser testar sem UI, via API:
curl -X POST http://localhost:8000/api/import-csv \
  -F "file=@test_produtos_simulacao_20itens.csv" \
  -F "regime_empresa=LUCRO_REAL" \
  -F "uf_origem=SP" \
  -F "uf_destino=RJ" \
  -F "cnae_principal=1413800"

# Response esperado:
{
  "lote_id": "uuid-aqui",
  "status": "PENDENTE",
  "total_itens": 20
}

# Depois pooling:
curl http://localhost:8000/api/lotes/{lote_id}/status
# Até status = CONCLUIDO

# Buscar itens:
curl http://localhost:8000/api/lotes/{lote_id}/itens
```

---

## 📚 Referências de NCM

**Vestiário (61, 62):**
- `61045090` - Camisetas de algodão
- `62034200` - Calças jeans masculinas
- `62063000` - Jaquetas
- `62033100` - Vestidos femininos
- `61159000` - Meias

**Alimentos (04, 07, 10, 19):**
- `04012100` - Leite integral
- `07133000` - Feijão
- `08081090` - Frutas (maçã)
- `10061000` - Arroz
- `19053000` - Pão e similar

**Farmacêutico (21, 30):**
- `21069090` - Vitaminas
- `30049010` - Medicamentos diversos

**Cosméticos (33):**
- `33041000` - Xampus
- `33072090` - Desodorantes

**Eletrônicos (84, 85, 90, 95):**
- `84716060` - Teclados
- `85183090` - Fones de ouvido
- `85443099` - Carregadores
- `85447090` - Cabos elétricos
- `90281090` - Câmeras digitais
- `95069090` - Pads e similares

---

**Última atualização:** 2026-04-09  
**Status:** Pronto para teste

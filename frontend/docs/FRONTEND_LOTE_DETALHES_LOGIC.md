# LoteDetalhes - Lógica de Implementação Frontend

**Data:** 2026-04-09  
**Arquivo:** `frontend/src/components/LoteDetalhes.jsx`  
**Propósito:** Documentar a lógica e padrões utilizados para exibir resultados da análise IA de itens fiscais

---

## 📋 Índice

1. [Arquitetura Geral](#arquitetura-geral)
2. [Componentes Reutilizáveis](#componentes-reutilizáveis)
3. [Fluxo de Dados](#fluxo-de-dados)
4. [Padrões de UI/UX](#padrões-de-uiux)
5. [Lógica de Filtros e Abas](#lógica-de-filtros-e-abas)
6. [Função de Export CSV](#função-de-export-csv)
7. [Oportunidades de Melhoria](#oportunidades-de-melhoria)

---

## Arquitetura Geral

```
LoteDetalhes (componente principal)
├── Header & Navegação
├── Cartões de Estatísticas (Total, Válidos, Divergentes, Benefícios)
├── Comparativo Fiscal (agregado por lote)
├── Sistema de Abas
│   ├── Aba: Todos os itens
│   ├── Aba: Apenas válidos
│   ├── Aba: Apenas divergentes
│   └── Aba: Com benefícios fiscais
└── Tabela de Resultados
    └── Componentes auxiliares (Tooltip, StatusBadge, ConfiancaBar, etc.)
```

### **Por que essa estrutura?**

1. **Separação de responsabilidades:** Cada componente tem uma função específica
2. **Reutilização:** Componentes como `Tooltip`, `StatusBadge` podem ser usados em outros lugares
3. **Performance:** React Query gerencia cache e refetch automático
4. **UX:** Abas permitem focar em um tipo de resultado por vez sem recarregar dados

---

## Componentes Reutilizáveis

### 1. **Tooltip**

```jsx
function Tooltip({ content, children }) {
  const [isVisible, setIsVisible] = useState(false)
  
  return (
    <div className="relative inline-block">
      <div onMouseEnter={() => setIsVisible(true)} ...>
        {children}
      </div>
      {isVisible && (
        <div className="absolute z-50 bottom-full left-1/2 ...">
          {content}
        </div>
      )}
    </div>
  )
}
```

**Uso:** Mostrar justificativas e artigos legais sem poluir a tabela  
**Vantagens:**
- Hover display economiza espaço
- Informação contextual disponível quando necessário
- Implementação agnóstica (funciona com qualquer conteúdo)

**Melhoria futura:** Considerar biblioteca como `@floating-ui/react` para melhor posicionamento em mobile.

---

### 2. **StatusBadge**

```jsx
function StatusBadge({ status }) {
  const styles = {
    VALIDO: 'bg-success-100 text-success-700',
    DIVERGENTE: 'bg-warning-100 text-warning-700',
  }
  return <span className={styles[status] || styles.DIVERGENTE}>
    {status === 'VALIDO' ? '✓' : '⚠'} {status}
  </span>
}
```

**Uso:** Indicar visualmente se um item passou na validação IA  
**Codificação visual (color coding):**
- Verde (✓ VALIDO) = item está correto conforme análise
- Amarelo (⚠ DIVERGENTE) = item teve mudanças sugeridas

**Princípio:** Usar cores + ícones + texto para acessibilidade máxima.

---

### 3. **ConfiancaBar**

```jsx
function ConfiancaBar({ valor }) {
  const percentual = Math.min(Math.max(valor || 0, 0), 100)
  let cor = 'bg-red-500'
  if (percentual >= 70) cor = 'bg-success-500'
  else if (percentual >= 50) cor = 'bg-warning-500'
  
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full ${cor}`} style={{ width: `${percentual}%` }}/>
      </div>
      <span>{percentual}%</span>
    </div>
  )
}
```

**Lógica:**
- `valor || 0`: Fallback para 0 se undefined
- `Math.min/max`: Garante valor dentro de [0, 100]
- Cores escalonadas: Red (0-50%) → Warning (50-70%) → Green (70-100%)

**Por que não usar barra de progresso nativa?** A barra customizada permite:
1. Cores dinâmicas baseadas em threshold
2. Tamanho fixo (não expande)
3. Controle fino de aparência

---

### 4. **DivergenciaNcm**

```jsx
function DivergenciaNcm({ ncmOriginal, ncmSugerido }) {
  if (ncmOriginal === ncmSugerido || !ncmSugerido) {
    return <span className="font-mono text-sm">{ncmOriginal}</span>
  }
  
  return (
    <div className="flex flex-col gap-1">
      <span className="font-mono text-sm line-through text-gray-400">{ncmOriginal}</span>
      <span className="font-mono text-sm font-bold text-warning-600">→ {ncmSugerido}</span>
    </div>
  )
}
```

**Design decision:**
- NCM em `font-mono` porque é código estruturado (8 dígitos)
- Mostra original e sugerido apenas se forem diferentes (evita redundância)
- Usa `→` para indicar mudança (visual intuitivo)

---

## Fluxo de Dados

### **React Query + Polling**

```jsx
const { data: lote, isLoading: loadingStatus } = useQuery({
  queryKey: ['lote', loteId],
  queryFn: () => getLoteStatus(loteId),
  refetchInterval: (query) => {
    const status = query.state?.data?.status
    return (status === 'PENDENTE' || status === 'PROCESSANDO') ? 3000 : false
  },
})

const isFinished = lote?.status === 'CONCLUIDO' || ...

const { data: itens } = useQuery({
  queryKey: ['itens', loteId],
  queryFn: () => getLoteItens(loteId),
  enabled: isFinished,  // ← Só executa quando isFinished = true
})
```

### **Por que essa abordagem?**

1. **Smart refetching:** Polling a cada 3s enquanto PENDENTE/PROCESSANDO, depois para
2. **Dependência:** Itens só são buscados depois que o lote terminar
3. **Cache automático:** React Query evita requests duplicadas
4. **Separação:** Cada query tem sua própria key para cache independente

### **Diagrama de estados:**

```
┌─────────────┐
│   PENDENTE  │ ← Polling 3s (status)
└──────┬──────┘
       │ refetch → PROCESSANDO
       ↓
┌─────────────────────┐
│  PROCESSANDO        │ ← Polling 3s (status)
│  Backend processando│
└──────┬──────────────┘
       │ refetch → CONCLUIDO
       ↓
┌──────────────────────────┐
│  CONCLUIDO               │ ← Para polling
│  enabled: true no itens  │ ← Dispara busca de itens
│  getData() chamado       │
└──────────────────────────┘
```

---

## Padrões de UI/UX

### **Cartões de Estatísticas**

```jsx
<div className="grid grid-cols-1 md:grid-cols-5 gap-4">
  <div>
    <p className="text-sm text-gray-600">Válidos</p>
    <p className="text-xl font-semibold text-success-600">{itensValidos.length}</p>
  </div>
  ...
</div>
```

**Padrão de card:**
1. Título descritivo (label em cinza pequeno)
2. Valor grande e legível (text-xl, semibold)
3. Cores específicas por categoria (success=verde, warning=amarelo, etc.)

**Responsividade:** `grid-cols-1 md:grid-cols-5`
- Mobile: 1 coluna (stack vertical)
- Desktop (md+): 5 colunas

---

### **Sistema de Abas**

```jsx
const [abaSelecionada, setAbaSelecionada] = useState('todos')

<div className="flex gap-2 mb-4 border-b border-gray-200">
  <button
    onClick={() => setAbaSelecionada('todos')}
    className={`px-4 py-2 font-medium border-b-2 transition-colors ${
      abaSelecionada === 'todos'
        ? 'border-primary-500 text-primary-600'
        : 'border-transparent text-gray-600 hover:text-gray-900'
    }`}
  >
    Todos ({itens?.length || 0})
  </button>
  ...
</div>

{abaSelecionada === 'todos' && renderizarTabela(itens)}
{abaSelecionada === 'validos' && renderizarTabela(itensValidos)}
```

**Design pattern:** Aba ativa tem:
- Borda inferior na cor primária
- Texto na cor primária
- Aba inativa tem borda transparente e texto cinza

**Vantagem:** Sem necessidade de bibliotecas extras (tabs nativos)

---

## Lógica de Filtros e Abas

### **Computação de arrays filtrados**

```jsx
const itensBeneficios = itens?.filter(item => item.possui_beneficio_fiscal) || []
const itensDivergentes = itens?.filter(item => item.status_validacao === 'DIVERGENTE') || []
const itensValidos = itens?.filter(item => item.status_validacao === 'VALIDO') || []
```

**Safe navigation:** `itens?.filter()` usa optional chaining para evitar erro se `itens` é undefined.  
**Fallback:** `|| []` garante que a variável é sempre um array (nunca undefined).

### **Performance consideration:**

Essas filtragens acontecem **a cada render**. Para muitos itens (> 10k), considerar:

```jsx
const itensBeneficios = useMemo(() => 
  itens?.filter(item => item.possui_beneficio_fiscal) || [], 
  [itens]
)
```

Isso calcula só quando `itens` muda.

---

## Função de Export CSV

### **Lógica passo-a-passo:**

```jsx
function exportarCsv(itens, loteInfo) {
  // 1. Validação
  if (!itens || itens.length === 0) {
    alert('Nenhum item para exportar')
    return
  }

  // 2. Define headers (primeira linha)
  const headers = [
    'Descrição', 'NCM Original', 'NCM Sugerido', 
    'Status', 'Confiança (%)', ...
  ]

  // 3. Mapeia cada item para array de valores
  const rows = itens.map(item => [
    item.descricao,
    item.ncm_original,
    item.ncm_sugerido || '-',  // Fallback para '-' se vazio
    ...
    (item.justificativa_ai || '').replace(/"/g, '""'),  // Escape quotes
  ])

  // 4. Monta CSV: headers + rows
  const csv = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n')

  // 5. Cria blob e download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `lote_${loteInfo?.id?.slice(0, 8)}_analise.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
```

### **Detalhes críticos:**

1. **Escape de quotes:** `replace(/"/g, '""')` segue o padrão CSV RFC 4180
   - Entrada: `"Leonardo da Vinci"`
   - Saída em CSV: `"""Leonardo da Vinci"""`
   - Ao abrir em Excel: mostra `"Leonardo da Vinci"` corretamente

2. **Wrapping de células:** Cada célula é envolvida em aspas duplas
   - Protege contra vírgulas dentro de valores
   - Exemplo: `"Camiseta, vermelha, grande"` fica como uma célula

3. **Blob + ObjectURL:**
   - Cria arquivo em memória (não faz upload)
   - `ObjectURL` cria uma URL local para o arquivo
   - Trigger de download é automático com `.click()`

4. **Limpeza:** Remove o elemento `<a>` do DOM após download

---

## Oportunidades de Melhoria

### **1. Performance - Memoization**

**Atual:**
```jsx
const itensBeneficios = itens?.filter(...) || []
```

**Melhor:**
```jsx
const itensBeneficios = useMemo(() => 
  itens?.filter(item => item.possui_beneficio_fiscal) || [], 
  [itens]
)
```

**Por quê:** Evita recompilação se `itens` não mudou.

---

### **2. Responsividade de Tabela**

**Atual:** Tabela com overflow horizontal em mobile (scrollbar).

**Melhor:** Componente responsivo que colapsa para card layout em mobile:

```jsx
// Em mobile: mostra como cards empilhados
// Em desktop: mostra como tabela tradicional
<Responsive.Table data={itens} columns={[...]} />
```

---

### **3. Paginação**

**Atual:** Tabela grande carrega tudo (pode ter 10k+ itens).

**Melhor:** Paginar com 50 itens por página:

```jsx
const [pagina, setPagina] = useState(1)
const itensPaginados = itens.slice((pagina - 1) * 50, pagina * 50)
```

---

### **4. Persistência de Aba**

**Atual:** Se recarregar a página, volta para aba "todos".

**Melhor:** Salvar em URL query parameter:

```jsx
const [abaSelecionada, setAbaSelecionada] = useSearchParams().get('aba') || 'todos'

// Ao mudar aba:
setSearchParams({ aba: 'beneficios' })
```

---

### **5. Sorting de Colunas**

**Adicionar:** Clicks em headers de coluna para ordenar

```jsx
const [sortBy, setSortBy] = useState('descricao')
const [sortOrder, setSortOrder] = useState('asc')

const itensOrdenados = itens.sort((a, b) => {
  const aVal = a[sortBy]
  const bVal = b[sortBy]
  return sortOrder === 'asc' ? aVal > bVal : aVal < bVal
})
```

---

### **6. Integração com Notificações**

**Adicionar:** Toast de sucesso ao exportar CSV:

```jsx
import { useToast } from '@chakra-ui/react'

const toast = useToast()

function exportarCsv(...) {
  ...
  toast({ title: 'Exportado!', status: 'success' })
}
```

---

### **7. Componentes de Filtro Avançado**

**Adicionar:** Sidebar com filtros:
- Filtrar por intervalo de confiança (slider)
- Filtrar por regime tributário (checkboxes)
- Filtrar por diferença de carga (range)

---

## Padrões de Codificação Utilizados

### ✅ **Boas práticas implementadas:**

| Prática | Exemplo |
|---------|---------|
| **Optional chaining** | `lote?.total_itens` |
| **Nullish coalescing** | `itens \|\| []` |
| **Computed properties** | `itensValidos = itens.filter(...)` |
| **Conditional rendering** | `{item.possui_beneficio_fiscal && <.../>}` |
| **Ternary operators** | `status === 'VALIDO' ? green : red` |
| **Array.map + filter** | `itens.map(i => ...).filter(...)` |
| **Event delegation** | `onClick={() => setAba('todos')}` |
| **CSS classes dinâmicas** | Template literals para classe condicional |

### ⚠️ **Anti-patterns evitados:**

| Anti-pattern | Evitar | Usar |
|---|---|---|
| Comparação direta com undefined | `if (x === undefined)` | `if (x === null \|\| x === undefined)` |
| Props drilling muito fundo | Passar por 5 níveis | Context API ou custom hooks |
| Renderização inline complexa | `{data.map(x => <Component x={x} y={y} z={z}.../>)}` | Extrair para função ou componente |
| State duplicado | `const [count, setCount]` e `const [doubled, setDoubled]` | Usar `useMemo` |

---

## Checklist para Manutenção Futura

- [ ] Testar com 10k+ itens (performance)
- [ ] Testar export CSV em Excel, Google Sheets, LibreOffice
- [ ] Testar em mobile (responsividade)
- [ ] Adicionar testes unitários para componentes auxiliares
- [ ] Documentar props de cada componente reutilizável
- [ ] Implementar error boundary
- [ ] Adicionar loading skeletons em lugar de spinners
- [ ] Melhorar acessibilidade (aria-labels, keyboard navigation)

---

## Conclusão

LoteDetalhes implementa uma interface moderna e intuitiva para análise de itens fiscais com:

✅ Componentes reutilizáveis e testáveis  
✅ Fluxo de dados eficiente com React Query  
✅ UX clara com sistema de abas  
✅ Export para análise externa  
✅ Responsividade básica  

**Próximas melhorias:** Paginação, sorting, filtros avançados, persistência de estado.

---

**Autor:** Claude (Senior Code Review)  
**Última atualização:** 2026-04-09  
**Status:** Production-ready com melhorias sugeridas

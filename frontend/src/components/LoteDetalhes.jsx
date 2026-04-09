import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle, Clock, AlertCircle, Loader2, Download, Info, TrendingDown, TrendingUp } from 'lucide-react'
import { useState } from 'react'
import { getLoteStatus, getLoteItens, getLoteComparativo } from '../services/api'

// Componente Tooltip reutilizável
function Tooltip({ content, children }) {
  const [isVisible, setIsVisible] = useState(false)

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="cursor-help"
      >
        {children}
      </div>
      {isVisible && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap max-w-xs">
          {content}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  )
}

// Componente Badge para Status
function StatusBadge({ status }) {
  const styles = {
    VALIDO: 'bg-success-100 text-success-700',
    DIVERGENTE: 'bg-warning-100 text-warning-700',
  }

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${styles[status] || styles.DIVERGENTE}`}>
      {status === 'VALIDO' ? '✓' : '⚠'} {status}
    </span>
  )
}

// Componente Barra de Confiança
function ConfiancaBar({ valor }) {
  const percentual = Math.min(Math.max(valor || 0, 0), 100)
  let cor = 'bg-red-500'
  if (percentual >= 70) cor = 'bg-success-500'
  else if (percentual >= 50) cor = 'bg-warning-500'

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${cor} transition-all`}
          style={{ width: `${percentual}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-gray-700">{percentual}%</span>
    </div>
  )
}

// Componente para exibir diferença de NCM
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

// Função para exportar CSV
function exportarCsv(itens, loteInfo) {
  if (!itens || itens.length === 0) {
    alert('Nenhum item para exportar')
    return
  }

  const headers = [
    'Descrição',
    'NCM Original',
    'NCM Sugerido',
    'CEST Original',
    'CEST Sugerido',
    'Status',
    'Confiança (%)',
    'Regime Tributário',
    'Carga Atual (%)',
    'Carga Reforma (%)',
    'Diferença R$',
    'IBS (%)',
    'CBS (%)',
    'Benefício Fiscal',
    'Tipo Benefício',
    'Justificativa',
  ]

  const rows = itens.map(item => [
    item.descricao,
    item.ncm_original,
    item.ncm_sugerido || '-',
    item.cest_original || '-',
    item.cest_sugerido || '-',
    item.status_validacao || '-',
    item.confianca_ai || '-',
    item.regime_tributario || '-',
    item.carga_atual_percentual || '-',
    item.carga_reforma_percentual || '-',
    item.diferenca_absoluta?.toFixed(2) || '-',
    item.aliquota_ibs || '-',
    item.aliquota_cbs || '-',
    item.possui_beneficio_fiscal ? 'Sim' : 'Não',
    item.tipo_beneficio || '-',
    (item.justificativa_ai || '').replace(/"/g, '""'), // Escape quotes para CSV
  ])

  const csv = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n')

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

function LoteDetalhes() {
  const { loteId } = useParams()
  const navigate = useNavigate()
  const [abaSelecionada, setAbaSelecionada] = useState('todos') // 'todos' | 'beneficios' | 'divergencias'

  const { data: lote, isLoading: loadingStatus } = useQuery({
    queryKey: ['lote', loteId],
    queryFn: () => getLoteStatus(loteId),
    refetchInterval: (query) => {
      const status = query.state?.data?.status
      return (status === 'PENDENTE' || status === 'PROCESSANDO') ? 3000 : false
    },
  })

  const isFinished = lote?.status === 'CONCLUIDO' || lote?.status === 'PROCESSADO' || lote?.status === 'ERRO'

  const { data: itens, isLoading: loadingItens } = useQuery({
    queryKey: ['itens', loteId],
    queryFn: () => getLoteItens(loteId),
    enabled: isFinished,
  })

  const { data: comparativo } = useQuery({
    queryKey: ['comparativo', loteId],
    queryFn: () => getLoteComparativo(loteId),
    enabled: isFinished,
  })

  // Filters
  const itensBeneficios = itens?.filter(item => item.possui_beneficio_fiscal) || []
  const itensDivergentes = itens?.filter(item => item.status_validacao === 'DIVERGENTE') || []
  const itensValidos = itens?.filter(item => item.status_validacao === 'VALIDO') || []

  const getStatusBadge = (status) => {
    const badges = {
      PENDENTE: { color: 'warning', icon: Clock, text: 'Aguardando...' },
      PROCESSANDO: { color: 'primary', icon: Loader2, text: 'Processando...' },
      CONCLUIDO: { color: 'success', icon: CheckCircle, text: 'Concluído' },
      PROCESSADO: { color: 'success', icon: CheckCircle, text: 'Concluído' },
      ERRO: { color: 'danger', icon: AlertCircle, text: 'Erro' },
    }

    const badge = badges[status] || badges.PENDENTE
    const Icon = badge.icon

    return (
      <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-${badge.color}-100 text-${badge.color}-700`}>
        <Icon className="w-4 h-4" />
        {badge.text}
      </span>
    )
  }

  if (loadingStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  const progress = lote?.total_itens > 0
    ? ((lote.itens_processados / lote.total_itens) * 100).toFixed(0)
    : 0

  const renderizarTabela = (dados) => {
    if (!dados || dados.length === 0) {
      return (
        <div className="flex items-center justify-center h-32 text-gray-500">
          Nenhum item para exibir
        </div>
      )
    }

    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Status</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Descrição</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">NCM</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">CEST</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Confiança</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Regime</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Carga Atual</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Carga Reforma</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Diferença</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Benefício</th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Justificativa</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {dados.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <StatusBadge status={item.status_validacao || 'DIVERGENTE'} />
                </td>
                <td className="px-4 py-3 max-w-xs truncate" title={item.descricao}>
                  {item.descricao}
                </td>
                <td className="px-4 py-3">
                  <DivergenciaNcm
                    ncmOriginal={item.ncm_original}
                    ncmSugerido={item.ncm_sugerido}
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-1">
                    <span className="font-mono text-xs text-gray-500">
                      {item.cest_original || '-'}
                    </span>
                    {item.cest_sugerido && item.cest_sugerido !== item.cest_original && (
                      <span className="font-mono text-xs font-bold text-warning-600">
                        → {item.cest_sugerido}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <ConfiancaBar valor={item.confianca_ai} />
                </td>
                <td className="px-4 py-3 text-xs">
                  <span className="px-2 py-1 bg-gray-100 rounded">
                    {item.regime_tributario || 'N/A'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-1 text-xs">
                    <span className="text-gray-600">{item.carga_atual_percentual ?? '-'}%</span>
                    <span className="text-gray-400 text-xs">ICMS+PIS+COFINS</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-1 text-xs">
                    <span className="text-primary-600 font-semibold">{item.carga_reforma_percentual ?? '-'}%</span>
                    <span className="text-gray-400 text-xs">IBS+CBS</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    {item.diferenca_absoluta && item.diferenca_absoluta < 0 ? (
                      <>
                        <TrendingDown className="w-4 h-4 text-success-600" />
                        <span className="font-semibold text-success-600">
                          -R$ {Math.abs(item.diferenca_absoluta).toFixed(2)}
                        </span>
                      </>
                    ) : item.diferenca_absoluta && item.diferenca_absoluta > 0 ? (
                      <>
                        <TrendingUp className="w-4 h-4 text-danger-600" />
                        <span className="font-semibold text-danger-600">
                          +R$ {item.diferenca_absoluta.toFixed(2)}
                        </span>
                      </>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  {item.possui_beneficio_fiscal ? (
                    <Tooltip content={item.artigo_legal || 'Benefício detectado'}>
                      <div className="flex items-center gap-1">
                        <CheckCircle className="w-4 h-4 text-success-600" />
                        <span className="text-success-600 font-semibold text-xs">
                          {item.tipo_beneficio}
                        </span>
                      </div>
                    </Tooltip>
                  ) : (
                    <span className="text-gray-400 text-xs">-</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {item.justificativa_ai ? (
                    <Tooltip content={item.justificativa_ai}>
                      <div className="flex items-center justify-center">
                        <Info className="w-4 h-4 text-primary-500 cursor-help" />
                      </div>
                    </Tooltip>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => navigate('/')}
        className="flex items-center gap-2 text-gray-600 hover:text-primary-500 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Voltar ao Dashboard
      </button>

      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Lote #{loteId?.slice(0, 8)}</h2>
          {getStatusBadge(lote?.status)}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600">Total de Itens</p>
            <p className="text-xl font-semibold">{lote?.total_itens || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Válidos</p>
            <p className="text-xl font-semibold text-success-600">{itensValidos.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Divergentes</p>
            <p className="text-xl font-semibold text-warning-600">{itensDivergentes.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Com Benefícios</p>
            <p className="text-xl font-semibold text-primary-600">{itensBeneficios.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Progresso</p>
            <p className="text-xl font-semibold">{progress}%</p>
          </div>
        </div>

        {(lote?.status === 'PENDENTE' || lote?.status === 'PROCESSANDO') && (
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {comparativo && (
        <div className="card mb-6">
          <h3 className="text-xl font-semibold mb-4">Comparativo Fiscal (Atual x Reforma)</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-600">Regime</p>
              <p className="text-base font-semibold">{comparativo.regime_empresa || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Rota Fiscal</p>
              <p className="text-base font-semibold">
                {(comparativo.uf_origem || '-')} → {(comparativo.uf_destino || '-')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">CNAE Principal</p>
              <p className="text-base font-semibold">{comparativo.cnae_principal || '-'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Base cálculo total</p>
              <p className="text-base font-semibold">R$ {comparativo.total_base_calculo?.toFixed(2)}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">Carga atual estimada</p>
              <p className="text-xl font-bold text-gray-900">R$ {comparativo.total_atual_estimado?.toFixed(2)}</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">Carga reforma estimada</p>
              <p className="text-xl font-bold text-gray-900">R$ {comparativo.total_reforma_estimado?.toFixed(2)}</p>
            </div>
            <div className={`rounded-lg p-4 ${comparativo.diferenca_absoluta < 0 ? 'bg-success-50' : 'bg-danger-50'}`}>
              <p className="text-sm text-gray-600">Diferença absoluta</p>
              <p className={`text-xl font-bold ${comparativo.diferenca_absoluta < 0 ? 'text-success-600' : 'text-danger-600'}`}>
                {comparativo.diferenca_absoluta < 0 ? '-' : '+'}R$ {Math.abs(comparativo.diferenca_absoluta).toFixed(2)}
              </p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">Diferença %</p>
              <p className="text-xl font-bold text-gray-900">{comparativo.diferenca_percentual?.toFixed(2)}%</p>
            </div>
          </div>

          <p className="text-sm text-gray-600 mt-3">
            Faixa de incerteza reforma: R$ {comparativo.faixa_incerteza_min?.toFixed(2)} a R$ {comparativo.faixa_incerteza_max?.toFixed(2)}
          </p>
        </div>
      )}

      {isFinished && itens && itens.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold">Resultados da Análise IA</h3>
            <button
              onClick={() => exportarCsv(itens, lote)}
              className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
            >
              <Download className="w-4 h-4" />
              Exportar CSV
            </button>
          </div>

          {/* Abas */}
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
            <button
              onClick={() => setAbaSelecionada('validos')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                abaSelecionada === 'validos'
                  ? 'border-success-500 text-success-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              ✓ Válidos ({itensValidos.length})
            </button>
            <button
              onClick={() => setAbaSelecionada('divergencias')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                abaSelecionada === 'divergencias'
                  ? 'border-warning-500 text-warning-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              ⚠ Divergências ({itensDivergentes.length})
            </button>
            <button
              onClick={() => setAbaSelecionada('beneficios')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                abaSelecionada === 'beneficios'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              💰 Benefícios ({itensBeneficios.length})
            </button>
          </div>

          {/* Conteúdo das abas */}
          {abaSelecionada === 'todos' && renderizarTabela(itens)}
          {abaSelecionada === 'validos' && renderizarTabela(itensValidos)}
          {abaSelecionada === 'divergencias' && renderizarTabela(itensDivergentes)}
          {abaSelecionada === 'beneficios' && (
            itensBeneficios.length > 0 ? (
              <div className="space-y-4">
                <div className="bg-primary-50 p-4 rounded-lg border border-primary-200">
                  <p className="text-sm text-primary-600">
                    ℹ️ {itensBeneficios.length} item(ns) com benefício(s) fiscal(is) identificado(s).
                    Clique na coluna "Benefício" para ver o artigo legal.
                  </p>
                </div>
                {renderizarTabela(itensBeneficios)}
              </div>
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-500">
                Nenhum item com benefício fiscal detectado
              </div>
            )
          )}
        </div>
      )}
    </div>
  )
}

export default LoteDetalhes

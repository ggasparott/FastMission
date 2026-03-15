import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react'
import { getLoteStatus, getLoteItens, getLoteComparativo } from '../services/api'

function LoteDetalhes() {
  const { loteId } = useParams()
  const navigate = useNavigate()

  const { data: lote, isLoading: loadingStatus } = useQuery({
    queryKey: ['lote', loteId],
    queryFn: () => getLoteStatus(loteId),
    refetchInterval: (query) => {
      const status = query.state?.data?.status
      // Continuar polling enquanto não estiver concluído ou com erro
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

  const getStatusBadge = (status) => {
    const badges = {
      PENDENTE: {
        color: 'warning',
        icon: Clock,
        text: 'Aguardando...',
      },
      PROCESSANDO: {
        color: 'primary',
        icon: Loader2,
        text: 'Processando...',
      },
      CONCLUIDO: {
        color: 'success',
        icon: CheckCircle,
        text: 'Concluído',
      },
      PROCESSADO: {
        color: 'success',
        icon: CheckCircle,
        text: 'Concluído',
      },
      ERRO: {
        color: 'danger',
        icon: AlertCircle,
        text: 'Erro',
      },
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
          <h2 className="text-2xl font-bold">Lote #{loteId}</h2>
          {getStatusBadge(lote?.status)}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600">Total de Itens</p>
            <p className="text-xl font-semibold">{lote?.total_itens || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Processados</p>
            <p className="text-xl font-semibold">{lote?.itens_processados || 0}</p>
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
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-sm text-gray-600">Diferença absoluta</p>
              <p className="text-xl font-bold text-gray-900">R$ {comparativo.diferenca_absoluta?.toFixed(2)}</p>
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
          <h3 className="text-xl font-semibold mb-4">Resultados da Análise</h3>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Descrição</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">NCM</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">CEST</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Regime</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Carga Atual</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Carga Reforma</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Δ R$</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">IBS</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">CBS</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Benefícios</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {itens.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{item.descricao}</td>
                    <td className="px-4 py-3 text-sm font-mono">{item.ncm_original}</td>
                    <td className="px-4 py-3 text-sm font-mono">{item.cest_original || '-'}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${
                        item.regime_tributario === 'NORMAL' ? 'bg-gray-100' :
                        item.regime_tributario === 'ALIQUOTA_REDUZIDA' ? 'bg-success-100 text-success-700' :
                        item.regime_tributario === 'CASHBACK' ? 'bg-primary-100 text-primary-700' :
                        'bg-warning-100 text-warning-700'
                      }`}>
                        {item.regime_tributario || 'N/A'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{item.carga_atual_percentual ?? '-'}%</td>
                    <td className="px-4 py-3 text-sm">{item.carga_reforma_percentual ?? '-'}%</td>
                    <td className="px-4 py-3 text-sm">R$ {item.diferenca_absoluta?.toFixed?.(2) ?? '-'}</td>
                    <td className="px-4 py-3 text-sm">{item.aliquota_ibs}%</td>
                    <td className="px-4 py-3 text-sm">{item.aliquota_cbs}%</td>
                    <td className="px-4 py-3 text-sm">
                      {item.possui_beneficio_fiscal ? (
                        <span className="text-success-600">✓ {item.tipo_beneficio}</span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default LoteDetalhes

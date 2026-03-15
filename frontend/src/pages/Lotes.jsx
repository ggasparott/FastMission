import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listLotes } from '../services/api'
import { FileText, Clock, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react'

const STATUS_CONFIG = {
  PENDENTE:    { label: 'Pendente',    color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  PROCESSANDO: { label: 'Processando', color: 'bg-blue-100 text-blue-800',   icon: Loader2 },
  CONCLUIDO:   { label: 'Concluído',   color: 'bg-green-100 text-green-800', icon: CheckCircle },
  ERRO:        { label: 'Erro',        color: 'bg-red-100 text-red-800',     icon: XCircle },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, color: 'bg-gray-100 text-gray-700', icon: AlertCircle }
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${cfg.color}`}>
      <Icon className={`w-3 h-3 ${status === 'PROCESSANDO' ? 'animate-spin' : ''}`} />
      {cfg.label}
    </span>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function Lotes() {
  const { data: lotes, isLoading, isError, refetch } = useQuery({
    queryKey: ['lotes'],
    queryFn: listLotes,
    refetchInterval: (data) => {
      const hasProcessing = data?.some?.((l) => l.status === 'PROCESSANDO' || l.status === 'PENDENTE')
      return hasProcessing ? 5000 : false
    },
  })

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lotes de Upload</h1>
          <p className="text-sm text-gray-500 mt-1">Histórico de arquivos importados e status de processamento</p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Loader2 className="w-4 h-4" />
          Atualizar
        </button>
      </div>

      {/* Estado de carregamento */}
      {isLoading && (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-8 h-8 animate-spin mr-3" />
          Carregando lotes...
        </div>
      )}

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          Erro ao carregar lotes. Verifique se a API está no ar.
        </div>
      )}

      {/* Tabela */}
      {lotes && lotes.length === 0 && (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-16 text-center text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">Nenhum lote encontrado</p>
          <p className="text-sm mt-1">Faça um upload de CSV no Dashboard para começar.</p>
          <Link to="/" className="mt-4 inline-block text-primary-600 hover:underline text-sm">
            Ir para o Dashboard →
          </Link>
        </div>
      )}

      {lotes && lotes.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Arquivo</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Status</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Regime</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Rota UF</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">CNAE</th>
                <th className="text-right px-4 py-3 font-semibold text-gray-600">Itens</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600">Enviado em</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {lotes.map((lote) => (
                <tr key={lote.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 font-medium text-gray-800">
                      <FileText className="w-4 h-4 text-gray-400 shrink-0" />
                      <span className="truncate max-w-xs" title={lote.nome_arquivo}>
                        {lote.nome_arquivo ?? 'sem nome'}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={lote.status} />
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {lote.regime_empresa
                      ? <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-mono">{lote.regime_empresa}</span>
                      : <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono text-xs">
                    {lote.uf_origem && lote.uf_destino
                      ? `${lote.uf_origem} → ${lote.uf_destino}`
                      : <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono text-xs">
                    {lote.cnae_principal ?? <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700">
                    {lote.total_itens ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                    {formatDate(lote.data_upload)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/lotes/${lote.id}`}
                      className="text-primary-600 hover:text-primary-800 font-medium text-xs whitespace-nowrap"
                    >
                      Ver detalhes →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

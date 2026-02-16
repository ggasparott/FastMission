import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import DashboardCards from '../components/DashboardCards'
import UploadCSV from '../components/UploadCSV'
import { getStats } from '../services/api'

function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    total_itens: 0,
    divergencias: 0,
    conformes: 0,
    economia: 0,
  })
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchStats = async () => {
    try {
      setRefreshing(true)
      const data = await getStats()
      setStats({
        total_itens: data.totalItens || 0,
        divergencias: data.divergencias || 0,
        conformes: (data.totalItens - data.divergencias) || 0,
        economia: data.economia || 0,
      })
    } catch (error) {
      console.error('Erro ao buscar estatísticas:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchStats()
    
    // Atualizar stats a cada 30 segundos
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleUploadSuccess = (loteId) => {
    navigate(`/lotes/${loteId}`)
    // Atualizar stats após upload
    setTimeout(fetchStats, 2000)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Dashboard - Reforma Tributária
          </h1>
          <p className="text-gray-600">
            Análise automática de cadastro para adequação ao IBS/CBS
          </p>
        </div>
        
        <button
          onClick={fetchStats}
          disabled={refreshing}
          className="btn-secondary flex items-center space-x-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Atualizar</span>
        </button>
      </div>

      <DashboardCards stats={stats} />
      <UploadCSV onUploadSuccess={handleUploadSuccess} />
    </div>
  )
}

export default Dashboard

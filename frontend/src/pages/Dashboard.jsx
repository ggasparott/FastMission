import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import DashboardCards from '../components/DashboardCards'
import UploadCSV from '../components/UploadCSV'

function Dashboard() {
  const navigate = useNavigate()
  const [stats] = useState({
    total_itens: 0,
    divergencias: 0,
    conformes: 0,
    economia: 0,
  })

  const handleUploadSuccess = (loteId) => {
    navigate(`/lotes/${loteId}`)
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Dashboard - Reforma Tributária
        </h1>
        <p className="text-gray-600">
          Análise automática de cadastro para adequação ao IBS/CBS
        </p>
      </div>

      <DashboardCards stats={stats} />
      <UploadCSV onUploadSuccess={handleUploadSuccess} />
    </div>
  )
}

export default Dashboard

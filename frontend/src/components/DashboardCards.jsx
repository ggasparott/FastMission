import { TrendingUp, AlertTriangle, CheckCircle, DollarSign } from 'lucide-react'

function DashboardCards({ stats }) {
  const cards = [
    {
      title: 'Total de Itens',
      value: stats?.total_itens || 0,
      icon: TrendingUp,
      color: 'primary',
    },
    {
      title: 'Divergências',
      value: stats?.divergencias || 0,
      icon: AlertTriangle,
      color: 'warning',
    },
    {
      title: 'Conformes',
      value: stats?.conformes || 0,
      icon: CheckCircle,
      color: 'success',
    },
    {
      title: 'Economia Potencial',
      value: `R$ ${(stats?.economia || 0).toLocaleString('pt-BR')}`,
      icon: DollarSign,
      color: 'success',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => {
        const Icon = card.icon
        return (
          <div key={index} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">{card.title}</p>
                <p className={`text-2xl font-bold text-${card.color}-600`}>
                  {card.value}
                </p>
              </div>
              <Icon className={`w-12 h-12 text-${card.color}-500 opacity-50`} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default DashboardCards

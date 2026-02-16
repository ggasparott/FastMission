import { Link } from 'react-router-dom'
import { Zap } from 'lucide-react'

function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <Zap className="w-8 h-8 text-primary-500" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">FastMission</h1>
              <p className="text-sm text-gray-500">Saneamento Cadastral</p>
            </div>
          </Link>
          
          <nav className="flex items-center gap-4">
            <Link 
              to="/" 
              className="text-gray-700 hover:text-primary-500 transition-colors"
            >
              Dashboard
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default Header

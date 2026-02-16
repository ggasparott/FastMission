import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

console.log('🔗 API URL:', API_URL)

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Interceptor de request - log e debug
api.interceptors.request.use(
  (config) => {
    console.log('📤 Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('❌ Request Error:', error)
    return Promise.reject(error)
  }
)

// Interceptor de response - log e tratamento de erros
api.interceptors.response.use(
  (response) => {
    console.log('✅ Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.status, error.message)
    if (error.response?.status === 404) {
      console.error('Recurso não encontrado:', error.config.url)
    }
    if (error.response?.status === 500) {
      console.error('Erro no servidor:', error.response.data)
    }
    return Promise.reject(error)
  }
)

export const uploadCSV = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  
  return response.data
}

export const getLoteStatus = async (loteId) => {
  const response = await api.get(`/lotes/${loteId}/status`)
  return response.data
}

export const getLoteItens = async (loteId) => {
  const response = await api.get(`/lotes/${loteId}/itens`)
  return response.data
}

export const getBeneficiosFiscais = async (loteId) => {
  const response = await api.get(`/lotes/${loteId}/beneficios-fiscais`)
  return response.data
}

export const getDivergenciasReforma = async (loteId) => {
  const response = await api.get(`/lotes/${loteId}/divergencias-reforma`)
  return response.data
}

// Novas funções para stats e health check
export const getStats = async () => {
  const response = await api.get('/stats')
  return response.data
}

export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}

export const fullHealthCheck = async () => {
  const response = await api.get('/health/full')
  return response.data
}

export default api

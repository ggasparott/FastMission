import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const uploadCSV = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await api.post('/upload', formData, {
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

export default api

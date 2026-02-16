import axios from 'axios';

// Pegar URL base SEM /api no final
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Garantir que sempre adiciona /api (e remove duplicatas)
const API_URL = API_BASE.replace(/\/api\/*$/, '') + '/api';

console.log('🔗 API Base:', API_BASE);
console.log('🔗 API URL Final:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Interceptor de request
api.interceptors.request.use(
  (config) => {
    console.log('📤 Request:', config.method?.toUpperCase(), config.url);
    console.log('📍 Full URL:', config.baseURL + config.url);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Interceptor de response
api.interceptors.response.use(
  (response) => {
    console.log('✅ Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.status, error.message);
    if (error.response?.status === 404) {
      console.error('Recurso não encontrado:', error.config.url);
      console.error('Full URL:', error.config.baseURL + error.config.url);
    }
    if (error.response?.status === 500) {
      console.error('Erro no servidor:', error.response.data);
    }
    return Promise.reject(error);
  }
);

// === LOTES ===
export const uploadCSV = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/import-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    console.error('❌ Erro no uploadCSV:', error);
    throw error;
  }
};

export const getLoteStatus = async (loteId) => {
  try {
    const response = await api.get(`/lotes/${loteId}/status`);
    return response.data;
  } catch (error) {
    console.error('❌ Erro ao buscar status do lote:', error);
    throw error;
  }
};

export const getLoteItens = async (loteId, params = {}) => {
  try {
    const response = await api.get(`/lotes/${loteId}/itens`, { params });
    return response.data;
  } catch (error) {
    console.error('❌ Erro ao buscar itens do lote:', error);
    throw error;
  }
};

export const listLotes = async (params = {}) => {
  try {
    const response = await api.get('/lotes', { params });
    return response.data;
  } catch (error) {
    console.error('❌ Erro ao listar lotes:', error);
    throw error;
  }
};

// === STATS ===
export const getStats = async () => {
  try {
    const response = await api.get('/stats');
    return response.data;
  } catch (error) {
    console.error('❌ Erro ao buscar estatísticas:', error);
    // Retornar dados mock em caso de erro
    return {
      totalLotes: 0,
      totalItens: 0,
      lotesPendentes: 0,
      lotesConcluidos: 0,
      divergencias: 0,
      beneficios: 0,
      economia: 0
    };
  }
};

// === HEALTH CHECK ===
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const fullHealthCheck = async () => {
  const response = await api.get('/health/full');
  return response.data;
};

export default api;
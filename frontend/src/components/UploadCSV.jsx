import { useState } from 'react'
import { Upload, AlertCircle, FileSpreadsheet } from 'lucide-react'
import { uploadCSV } from '../services/api'

function UploadCSV({ onUploadSuccess }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [empresaContexto, setEmpresaContexto] = useState({
    regime_empresa: 'SIMPLES',
    uf_origem: 'SP',
    uf_destino: 'SP',
    cnae_principal: '',
  })

  const handleContextoChange = (e) => {
    const { name, value } = e.target
    setEmpresaContexto((prev) => ({ ...prev, [name]: value }))
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange({ target: { files: e.dataTransfer.files } })
    }
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Por favor, selecione um arquivo CSV')
        return
      }
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Por favor, selecione um arquivo CSV')
      return
    }

    if (!empresaContexto.cnae_principal.trim()) {
      setError('Informe o CNAE principal da empresa')
      return
    }

    setUploading(true)
    setError(null)

    try {
      console.log('📤 Iniciando upload:', file.name)
      const response = await uploadCSV(file, empresaContexto)
      console.log('✅ Upload concluído:', response)
      onUploadSuccess(response.lote_id)
      setFile(null)
      
      // Resetar input
      const fileInput = document.getElementById('file-upload')
      if (fileInput) fileInput.value = ''
    } catch (err) {
      console.error('❌ Upload error:', err)
      
      // Mensagens de erro específicas
      if (!err.response) {
        setError('❌ Erro de conexão. Verifique se o backend está rodando ou desabilite extensões de bloqueio (AdBlock, uBlock).')
      } else if (err.response?.status === 400) {
        setError(`❌ Arquivo inválido: ${err.response?.data?.detail || 'formato incorreto'}`)
      } else if (err.response?.status === 413) {
        setError('❌ Arquivo muito grande. Máximo permitido: 50MB')
      } else if (err.response?.status === 500) {
        setError('❌ Erro no servidor. Tente novamente em alguns instantes.')
      } else {
        setError(`❌ Erro ao fazer upload: ${err.response?.data?.detail || err.message}`)
      }
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">Upload de Cadastro</h2>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Regime</label>
          <select
            className="input"
            name="regime_empresa"
            value={empresaContexto.regime_empresa}
            onChange={handleContextoChange}
          >
            <option value="SIMPLES">SIMPLES</option>
            <option value="LUCRO_PRESUMIDO">LUCRO_PRESUMIDO</option>
            <option value="LUCRO_REAL">LUCRO_REAL</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">UF Origem</label>
          <input
            className="input"
            name="uf_origem"
            maxLength={2}
            value={empresaContexto.uf_origem}
            onChange={handleContextoChange}
            placeholder="SP"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">UF Destino</label>
          <input
            className="input"
            name="uf_destino"
            maxLength={2}
            value={empresaContexto.uf_destino}
            onChange={handleContextoChange}
            placeholder="RJ"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">CNAE Principal</label>
          <input
            className="input"
            name="cnae_principal"
            value={empresaContexto.cnae_principal}
            onChange={handleContextoChange}
            placeholder="4711301"
          />
        </div>
      </div>
      
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center gap-4">
          {file ? (
            <FileSpreadsheet className="w-16 h-16 text-success-500" />
          ) : (
            <Upload className="w-16 h-16 text-gray-400" />
          )}
          
          <div>
            <p className="text-lg font-medium text-gray-700">
              {file ? file.name : 'Arraste seu arquivo CSV aqui'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              ou clique para selecionar
            </p>
          </div>

          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          
          <label
            htmlFor="file-upload"
            className="btn btn-primary cursor-pointer"
          >
            Selecionar Arquivo
          </label>

          {file && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn btn-success w-full"
            >
              {uploading ? 'Processando...' : 'Iniciar Análise'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-danger-50 border border-danger-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-danger-500 flex-shrink-0 mt-0.5" />
          <p className="text-danger-700">{error}</p>
        </div>
      )}

      <div className="mt-4 text-sm text-gray-600">
        <p className="font-medium mb-2">Formato esperado do CSV:</p>
        <code className="block bg-gray-100 p-2 rounded">
          descricao,ncm,cest,quantidade,valor_unitario<br />
          Arroz Integral,1006.30.21,17.069.00,120,24.90<br />
          Leite UHT,0401.10.10,17.002.00,80,6.49
        </code>
      </div>
    </div>
  )
}

export default UploadCSV

import { useState } from 'react'
import { Upload, AlertCircle, FileSpreadsheet } from 'lucide-react'
import { uploadCSV } from '../services/api'

function UploadCSV({ onUploadSuccess }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)

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
      setError('Selecione um arquivo primeiro')
      return
    }

    setUploading(true)
    setError(null)

    try {
      console.log('📤 Uploading file:', file.name)
      const response = await uploadCSV(file)
      console.log('✅ Upload success:', response)
      onUploadSuccess(response.lote_id)
      setFile(null)
      
      // Resetar input
      const fileInput = document.getElementById('file-upload')
      if (fileInput) fileInput.value = ''
    } catch (err) {
      console.error('❌ Upload error:', err)
      const errorMessage = err.response?.data?.detail 
        || err.message 
        || 'Erro ao fazer upload do arquivo'
      setError(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">Upload de Cadastro</h2>
      
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
          descricao,ncm,cest<br />
          Arroz Integral,1006.30.21,17.069.00<br />
          Leite UHT,0401.10.10,17.002.00
        </code>
      </div>
    </div>
  )
}

export default UploadCSV

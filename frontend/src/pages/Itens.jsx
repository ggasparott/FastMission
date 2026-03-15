import { useEffect, useMemo, useState } from 'react'
import { Pencil, Plus, Save, Trash2, X } from 'lucide-react'
import {
  createItem,
  deleteItem,
  listItens,
  updateItem,
} from '../services/api'

const initialForm = {
  descricao: '',
  ncm: '',
  cest: '',
  sku: '',
  ean_gtin: '',
  cfop: '',
  origem_produto: '',
  cst_csosn: '',
  aliquota_icms: '',
  aliquota_pis: '',
  aliquota_cofins: '',
  possui_st: '',
  quantidade: '',
  valor_unitario: '',
}

function Itens() {
  const [itens, setItens] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [editingId, setEditingId] = useState(null)

  const [filters, setFilters] = useState({
    sku: '',
    ncm: '',
    cfop: '',
    possui_st: '',
  })

  const [form, setForm] = useState(initialForm)

  const hasActiveFilter = useMemo(
    () => Object.values(filters).some((value) => value && value.trim() !== ''),
    [filters]
  )

  const normalizePayload = (raw) => {
    const payload = {
      descricao: raw.descricao?.trim() || undefined,
      ncm: raw.ncm?.trim() || undefined,
      cest: raw.cest?.trim() || undefined,
      sku: raw.sku?.trim() || undefined,
      ean_gtin: raw.ean_gtin?.trim() || undefined,
      cfop: raw.cfop?.trim() || undefined,
      origem_produto:
        raw.origem_produto === '' ? undefined : Number(raw.origem_produto),
      cst_csosn: raw.cst_csosn?.trim() || undefined,
      aliquota_icms:
        raw.aliquota_icms === '' ? undefined : Number(raw.aliquota_icms),
      aliquota_pis: raw.aliquota_pis === '' ? undefined : Number(raw.aliquota_pis),
      aliquota_cofins:
        raw.aliquota_cofins === '' ? undefined : Number(raw.aliquota_cofins),
      possui_st: raw.possui_st?.trim() || undefined,
      quantidade: raw.quantidade === '' ? undefined : Number(raw.quantidade),
      valor_unitario: raw.valor_unitario === '' ? undefined : Number(raw.valor_unitario),
    }

    if (!payload.descricao || !payload.ncm) {
      throw new Error('Descrição e NCM são obrigatórios.')
    }

    return payload
  }

  const fetchItens = async (currentFilters = filters) => {
    try {
      setErro('')
      setLoading(true)

      const query = {
        skip: 0,
        limit: 100,
      }

      if (currentFilters.sku) query.sku = currentFilters.sku
      if (currentFilters.ncm) query.ncm = currentFilters.ncm
      if (currentFilters.cfop) query.cfop = currentFilters.cfop
      if (currentFilters.possui_st) query.possui_st = currentFilters.possui_st

      const data = await listItens(query)
      setItens(data)
    } catch (error) {
      const detail = error?.response?.data?.detail
      setErro(typeof detail === 'string' ? detail : 'Erro ao carregar itens.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchItens()
  }, [])

  const resetForm = () => {
    setForm(initialForm)
    setEditingId(null)
  }

  const handleFilterChange = (event) => {
    const { name, value } = event.target
    setFilters((prev) => ({ ...prev, [name]: value }))
  }

  const handleFormChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleBuscar = async (event) => {
    event.preventDefault()
    await fetchItens(filters)
  }

  const handleLimparFiltros = async () => {
    const clean = {
      sku: '',
      ncm: '',
      cfop: '',
      possui_st: '',
    }
    setFilters(clean)
    await fetchItens(clean)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setErro('')
    setSucesso('')

    try {
      setSubmitting(true)
      const payload = normalizePayload(form)

      if (editingId) {
        await updateItem(editingId, payload)
        setSucesso('Item atualizado com sucesso.')
      } else {
        await createItem(payload)
        setSucesso('Item criado com sucesso.')
      }

      resetForm()
      await fetchItens()
    } catch (error) {
      const detail = error?.response?.data?.detail
      setErro(typeof detail === 'string' ? detail : error.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleEditar = (item) => {
    setSucesso('')
    setErro('')
    setEditingId(item.id)
    setForm({
      descricao: item.descricao || '',
      ncm: item.ncm_original || '',
      cest: item.cest_original || '',
      sku: item.sku || '',
      ean_gtin: item.ean_gtin || '',
      cfop: item.cfop || '',
      origem_produto:
        item.origem_produto === null || item.origem_produto === undefined
          ? ''
          : String(item.origem_produto),
      cst_csosn: item.cst_csosn || '',
      aliquota_icms:
        item.aliquota_icms === null || item.aliquota_icms === undefined
          ? ''
          : String(item.aliquota_icms),
      aliquota_pis:
        item.aliquota_pis === null || item.aliquota_pis === undefined
          ? ''
          : String(item.aliquota_pis),
      aliquota_cofins:
        item.aliquota_cofins === null || item.aliquota_cofins === undefined
          ? ''
          : String(item.aliquota_cofins),
      possui_st: item.possui_st || '',
      quantidade:
        item.quantidade === null || item.quantidade === undefined
          ? ''
          : String(item.quantidade),
      valor_unitario:
        item.valor_unitario === null || item.valor_unitario === undefined
          ? ''
          : String(item.valor_unitario),
    })
  }

  const handleDelete = async (item) => {
    const confirmado = window.confirm(
      `Deseja excluir o item ${item.sku || item.id}?`
    )

    if (!confirmado) return

    try {
      setErro('')
      setSucesso('')
      await deleteItem(item.id)
      setSucesso('Item excluído com sucesso.')
      await fetchItens()
    } catch (error) {
      const detail = error?.response?.data?.detail
      setErro(typeof detail === 'string' ? detail : 'Erro ao excluir item.')
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Itens Manuais</h1>
        <p className="text-gray-600 mt-1">
          Cadastro, edição e exclusão de itens para o módulo de varejo.
        </p>
      </div>

      {erro && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
          {erro}
        </div>
      )}

      {sucesso && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-700">
          {sucesso}
        </div>
      )}

      <section className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Filtros</h2>
        <form className="grid grid-cols-1 md:grid-cols-5 gap-4" onSubmit={handleBuscar}>
          <input
            className="input"
            name="sku"
            value={filters.sku}
            onChange={handleFilterChange}
            placeholder="SKU"
          />
          <input
            className="input"
            name="ncm"
            value={filters.ncm}
            onChange={handleFilterChange}
            placeholder="NCM"
          />
          <input
            className="input"
            name="cfop"
            value={filters.cfop}
            onChange={handleFilterChange}
            placeholder="CFOP"
          />
          <select
            className="input"
            name="possui_st"
            value={filters.possui_st}
            onChange={handleFilterChange}
          >
            <option value="">Possui ST?</option>
            <option value="SIM">SIM</option>
            <option value="NAO">NAO</option>
          </select>
          <div className="flex gap-2">
            <button className="btn btn-primary w-full" type="submit">
              Buscar
            </button>
            <button
              className="btn w-full border border-gray-300 text-gray-700 hover:bg-gray-100"
              type="button"
              onClick={handleLimparFiltros}
              disabled={!hasActiveFilter}
            >
              Limpar
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {editingId ? 'Editar Item' : 'Novo Item'}
          </h2>
          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="btn border border-gray-300 text-gray-700 hover:bg-gray-100 flex items-center gap-2"
            >
              <X className="w-4 h-4" />
              Cancelar edição
            </button>
          )}
        </div>

        <form className="grid grid-cols-1 md:grid-cols-4 gap-4" onSubmit={handleSubmit}>
          <div className="md:col-span-2">
            <label className="block text-sm text-gray-700 mb-1">Descrição *</label>
            <input
              className="input"
              name="descricao"
              value={form.descricao}
              onChange={handleFormChange}
              placeholder="Descrição do item"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">NCM *</label>
            <input
              className="input"
              name="ncm"
              value={form.ncm}
              onChange={handleFormChange}
              placeholder="00000000"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">CEST</label>
            <input
              className="input"
              name="cest"
              value={form.cest}
              onChange={handleFormChange}
              placeholder="0000000"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">SKU</label>
            <input
              className="input"
              name="sku"
              value={form.sku}
              onChange={handleFormChange}
              placeholder="SKU-001"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">EAN/GTIN</label>
            <input
              className="input"
              name="ean_gtin"
              value={form.ean_gtin}
              onChange={handleFormChange}
              placeholder="7891234567890"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">CFOP</label>
            <input
              className="input"
              name="cfop"
              value={form.cfop}
              onChange={handleFormChange}
              placeholder="5102"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">Origem</label>
            <input
              className="input"
              name="origem_produto"
              type="number"
              min="0"
              max="8"
              value={form.origem_produto}
              onChange={handleFormChange}
              placeholder="0"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">CST/CSOSN</label>
            <input
              className="input"
              name="cst_csosn"
              value={form.cst_csosn}
              onChange={handleFormChange}
              placeholder="060"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">Alíquota ICMS</label>
            <input
              className="input"
              name="aliquota_icms"
              type="number"
              step="0.01"
              value={form.aliquota_icms}
              onChange={handleFormChange}
              placeholder="18.00"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">Alíquota PIS</label>
            <input
              className="input"
              name="aliquota_pis"
              type="number"
              step="0.01"
              value={form.aliquota_pis}
              onChange={handleFormChange}
              placeholder="1.65"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">Alíquota COFINS</label>
            <input
              className="input"
              name="aliquota_cofins"
              type="number"
              step="0.01"
              value={form.aliquota_cofins}
              onChange={handleFormChange}
              placeholder="7.60"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">Possui ST</label>
            <select
              className="input"
              name="possui_st"
              value={form.possui_st}
              onChange={handleFormChange}
            >
              <option value="">Selecione</option>
              <option value="SIM">SIM</option>
              <option value="NAO">NAO</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">Quantidade</label>
            <input
              className="input"
              name="quantidade"
              type="number"
              step="0.01"
              value={form.quantidade}
              onChange={handleFormChange}
              placeholder="10"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">Valor Unitário</label>
            <input
              className="input"
              name="valor_unitario"
              type="number"
              step="0.01"
              value={form.valor_unitario}
              onChange={handleFormChange}
              placeholder="12.50"
            />
          </div>

          <div className="md:col-span-4 flex justify-end">
            <button
              type="submit"
              className="btn btn-primary flex items-center gap-2"
              disabled={submitting}
            >
              {editingId ? <Save className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
              {submitting
                ? 'Salvando...'
                : editingId
                ? 'Salvar Alterações'
                : 'Cadastrar Item'}
            </button>
          </div>
        </form>
      </section>

      <section className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Itens Cadastrados ({itens.length})
        </h2>

        {loading ? (
          <p className="text-gray-600">Carregando itens...</p>
        ) : itens.length === 0 ? (
          <p className="text-gray-600">Nenhum item encontrado.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-600">
                  <th className="py-2 pr-3">SKU</th>
                  <th className="py-2 pr-3">Descrição</th>
                  <th className="py-2 pr-3">NCM</th>
                  <th className="py-2 pr-3">CFOP</th>
                  <th className="py-2 pr-3">ST</th>
                  <th className="py-2 pr-3">Status</th>
                  <th className="py-2">Ações</th>
                </tr>
              </thead>
              <tbody>
                {itens.map((item) => (
                  <tr key={item.id} className="border-b last:border-0">
                    <td className="py-2 pr-3">{item.sku || '-'}</td>
                    <td className="py-2 pr-3">{item.descricao}</td>
                    <td className="py-2 pr-3">{item.ncm_original}</td>
                    <td className="py-2 pr-3">{item.cfop || '-'}</td>
                    <td className="py-2 pr-3">{item.possui_st || '-'}</td>
                    <td className="py-2 pr-3">{item.status_validacao}</td>
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <button
                          className="btn border border-gray-300 text-gray-700 hover:bg-gray-100 px-3 py-1 text-xs flex items-center gap-1"
                          onClick={() => handleEditar(item)}
                        >
                          <Pencil className="w-3 h-3" />
                          Editar
                        </button>
                        <button
                          className="btn border border-red-200 text-red-700 hover:bg-red-50 px-3 py-1 text-xs flex items-center gap-1"
                          onClick={() => handleDelete(item)}
                        >
                          <Trash2 className="w-3 h-3" />
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

export default Itens

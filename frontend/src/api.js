import axios from 'axios'

export const api = axios.create({ baseURL: '/api', timeout: 360000 })

export const listTools    = () => api.get('/tools').then(r => r.data)
export const getConfig    = () => api.get('/config').then(r => r.data)
export const saveConfig   = (llm) => api.post('/config', llm).then(r => r.data)
export const getBrand     = () => api.get('/brand').then(r => r.data)
export const saveBrand    = (brand) => api.post('/brand', brand).then(r => r.data)
export const resetBrand   = (preset) => api.post(`/brand/reset?preset=${preset}`).then(r => r.data)
export const analyzeRelations = (p) => api.post('/tools/relations/analyze', p).then(r => r.data)
export const analyzeAffinity  = (p) => api.post('/tools/affinity/analyze',  p).then(r => r.data)
export const analyzePareto    = (p) => api.post('/tools/pareto/analyze',    p).then(r => r.data)
export const analyzeRadar     = (p) => api.post('/tools/radar/analyze',     p).then(r => r.data)
export const analyzeW5H2      = (p) => api.post('/tools/w5h2/analyze',      p).then(r => r.data)
export const analyzeRca       = (p) => api.post('/tools/rca/analyze',       p).then(r => r.data)
export const analyzeFishbone  = (p) => api.post('/tools/fishbone/analyze',  p).then(r => r.data)
export const analyzeQccGuide  = (p) => api.post('/tools/qcc_guide/analyze', p).then(r => r.data)

// 通用: 下载文件（pptx / xlsx / …）
export async function downloadFile(tool, format, payload, filename) {
  const r = await api.post(`/tools/${tool}/export/${format}`, payload, { responseType: 'blob' })
  const url = URL.createObjectURL(r.data)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// 兼容旧调用
export const downloadPptx = (tool, payload, filename) =>
  downloadFile(tool, 'pptx', payload, filename)
export const downloadXlsx = (tool, payload, filename) =>
  downloadFile(tool, 'xlsx', payload, filename)

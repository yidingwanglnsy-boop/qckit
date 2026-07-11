import axios from 'axios'

export const api = axios.create({ baseURL: '/api', timeout: 360000 })

export const listTools    = () => api.get('/tools').then(r => r.data)
export const getConfig    = () => api.get('/config').then(r => r.data)
export const saveConfig   = (llm) => api.post('/config', llm).then(r => r.data)
export const analyzeRelations = (p) => api.post('/tools/relations/analyze', p).then(r => r.data)
export const analyzeAffinity  = (p) => api.post('/tools/affinity/analyze',  p).then(r => r.data)
export const analyzePareto    = (p) => api.post('/tools/pareto/analyze',    p).then(r => r.data)

// 通用: 下载 PPTX
export async function downloadPptx(tool, payload, filename) {
  const r = await api.post(`/tools/${tool}/export/pptx`, payload, { responseType: 'blob' })
  const url = URL.createObjectURL(r.data)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

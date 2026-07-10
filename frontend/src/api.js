import axios from 'axios'

export const api = axios.create({ baseURL: '/api', timeout: 180000 })

export const listTools    = () => api.get('/tools').then(r => r.data)
export const getConfig    = () => api.get('/config').then(r => r.data)
export const saveConfig   = (llm) => api.post('/config', llm).then(r => r.data)
export const analyzeRelations = (payload) =>
  api.post('/tools/relations/analyze', payload).then(r => r.data)

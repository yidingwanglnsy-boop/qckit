import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'

export const api = axios.create({ baseURL: '/api', timeout: 360000 })

// —— 全局错误提示: LLM 超时 / 网络 / 后端错误 ——————————————————————————
let lastNoticeAt = 0
function notify (type, title, message) {
  // 5 秒内同类型不重复弹, 避免刷屏
  const now = Date.now()
  if (now - lastNoticeAt < 800) return
  lastNoticeAt = now
  ElNotification({ type, title, message, duration: 6000, position: 'bottom-right' })
}

api.interceptors.response.use(
  r => r,
  err => {
    const url = err.config?.url || '?'
    // 超时
    if (err.code === 'ECONNABORTED' || /timeout/i.test(err.message)) {
      notify('warning', 'AI 分析超时',
        `请求 ${url} 超过 ${Math.round((err.config?.timeout || 0) / 1000)} 秒未响应。可能原因：\n` +
        `· LLM 服务过载或网络慢\n· 输入内容过多\n\n建议：稍后重试；或在【设置】里更换更快的模型。`)
      return Promise.reject(err)
    }
    // 无响应 (网络断/后端未启动)
    if (!err.response) {
      notify('error', '无法连接后端',
        `请求 ${url} 未收到响应。请检查后端服务是否已启动（默认 http://localhost:8000）。`)
      return Promise.reject(err)
    }
    // HTTP 错误 - 优先解析结构化 detail (error_code + message + hint)
    const status = err.response.status
    const d = err.response.data?.detail
    const structured = d && typeof d === 'object' && d.message
    const body = structured
      ? `${d.message}${d.hint ? '\n\n💡 ' + d.hint : ''}`
      : String(d || err.response.data?.message || err.response.statusText || '未知错误')
    const code = structured ? d.error_code : ''

    if (code === 'LLM_AUTH' || status === 401 || status === 403) {
      notify('error', 'AI 密钥无效或未授权', body)
    } else if (code === 'LLM_RATE_LIMIT' || status === 429) {
      notify('warning', 'AI 服务限流', body)
    } else if (code === 'LLM_TIMEOUT' || status === 504) {
      notify('warning', 'AI 响应超时', body)
    } else if (code === 'LLM_UNREACHABLE' || status === 503) {
      notify('error', '无法连接 AI 服务', body)
    } else if (code === 'LLM_BAD_JSON' || status === 502) {
      notify('warning', 'AI 返回格式异常', body)
    } else if (status >= 500) {
      notify('error', '后端服务错误', `${body}\n\n如反复出现，请查看后端日志。`)
    } else {
      notify('error', `请求失败 (${status})`, body)
    }
    return Promise.reject(err)
  }
)

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
export const analyzeTree      = (p) => api.post('/tools/tree/analyze',      p).then(r => r.data)
export const analyzeMatrix    = (p) => api.post('/tools/matrix/analyze',    p).then(r => r.data)
export const analyzeMda       = (p) => api.post('/tools/mda/analyze',       p).then(r => r.data)
export const analyzePdpc      = (p) => api.post('/tools/pdpc/analyze',      p).then(r => r.data)
export const analyzeArrow     = (p) => api.post('/tools/arrow/analyze',     p).then(r => r.data)

// 通用: 下载文件（pptx / xlsx / …）
export async function downloadFile (tool, format, payload, filename) {
  try {
    const r = await api.post(`/tools/${tool}/export/${format}`, payload,
      { responseType: 'blob' })
    // 后端可能返回 JSON 错误但状态码 200(极少)
    if (r.data.type === 'application/json') {
      const text = await r.data.text()
      ElMessage.error(`导出失败: ${text}`)
      return
    }
    const url = URL.createObjectURL(r.data)
    const a = document.createElement('a')
    a.href = url; a.download = filename; a.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
    ElMessage.success(`已导出 ${filename}`)
  } catch (e) {
    // 拦截器已弹 notification, 这里只兜底
    console.error('[downloadFile]', e)
  }
}

// 兼容旧调用
export const downloadPptx = (tool, payload, filename) =>
  downloadFile(tool, 'pptx', payload, filename)
export const downloadXlsx = (tool, payload, filename) =>
  downloadFile(tool, 'xlsx', payload, filename)

/**
 * 统一"示例 + 历史"组合式：
 *   const tk = useToolkit('relations', form) // form 是响应式对象
 *   tk.loadSample('welding')     // 一键填充示例
 *   tk.saveHistory({...result})  // 分析成功后调用, 存 localStorage
 *   tk.history                   // 该工具最近 10 条 (响应式)
 *   tk.restoreHistory(id)        // 恢复历史条目到 form
 *   tk.samples                   // 该工具的示例列表
 */
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { SAMPLES } from './samples.js'

const HIST_KEY_PREFIX = 'qckit.history.'
const HIST_MAX = 10

function loadStore (tool) {
  try {
    const raw = localStorage.getItem(HIST_KEY_PREFIX + tool)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}
function saveStore (tool, list) {
  try { localStorage.setItem(HIST_KEY_PREFIX + tool, JSON.stringify(list)) } catch {}
}

export function useToolkit (tool, formRef) {
  const samples = SAMPLES[tool] || []
  const history = ref(loadStore(tool))

  function loadSample (id) {
    const s = samples.find(x => x.id === id) || samples[0]
    if (!s) return ElMessage.warning('该工具暂无示例数据')
    // 深拷贝, 避免污染示例源
    Object.assign(formRef, JSON.parse(JSON.stringify(s.data)))
    ElMessage.success(`已填入示例：${s.name}`)
  }

  function saveHistory (result, snapshot = null) {
    // snapshot: 输入数据的快照; 若未传, 尝试序列化 formRef
    let snap
    try { snap = snapshot ? JSON.parse(JSON.stringify(snapshot))
                          : JSON.parse(JSON.stringify(formRef)) } catch { snap = {} }
    const entry = {
      id: Date.now(),
      title: snap.topic || snap.problem || snap.subject || '(未命名)',
      snapshot: snap,
      resultPreview: summarize(result),
      at: new Date().toISOString(),
    }
    history.value = [entry, ...history.value].slice(0, HIST_MAX)
    saveStore(tool, history.value)
  }

  function restoreHistory (id) {
    const h = history.value.find(x => x.id === id)
    if (!h) return
    Object.assign(formRef, JSON.parse(JSON.stringify(h.snapshot)))
    ElMessage.success(`已恢复历史：${h.title}`)
  }

  function clearHistory () {
    history.value = []
    saveStore(tool, [])
    ElMessage.info('历史已清空')
  }

  function summarize (r) {
    if (!r) return ''
    // 各工具的关键字段
    if (r.summary) return r.summary.slice(0, 60)
    if (r.insights) return r.insights.slice(0, 60)
    if (r.root_cause) return r.root_cause.slice(0, 60)
    if (r.goal) return r.goal.slice(0, 60)
    return JSON.stringify(r).slice(0, 60)
  }

  return { samples, history, loadSample, saveHistory, restoreHistory, clearHistory }
}

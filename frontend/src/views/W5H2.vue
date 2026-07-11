<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#dc2626"><Grid /></el-icon>
        <div>
          <div class="tb-title">5W2H 分析</div>
          <div class="tb-sub">根因驱动的对策展开：Why 必填，其余字段可让 AI 联想补全</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button size="default" :disabled="!hasResult" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button size="default" :disabled="!hasResult"
          :loading="pptxLoading" @click="exportPptx">
          <el-icon><Document /></el-icon>&nbsp;PPTX
        </el-button>
      </div>
    </div>

    <div class="qc-panel">
      <div class="qc-panel-hd">
        <span>📝 5W2H 表单</span>
        <div style="display:flex;gap:8px;align-items:center;">
          <el-checkbox v-model="useLlm" size="small">未填字段用 AI 补全</el-checkbox>
          <el-button size="small" @click="loadSample">
            <el-icon><Files /></el-icon>&nbsp;示例
          </el-button>
        </div>
      </div>

      <el-form label-position="top" size="default" class="qc-form">
        <el-form-item label="主题">
          <el-input v-model="form.topic" placeholder="如：焊接工序不良率偏高" />
        </el-form-item>
      </el-form>

      <!-- 5W2H 田字格：Why 居中 (跨两列)，六项环绕 -->
      <div class="w5h2-grid">
        <div v-for="f in orderTop" :key="f.key" class="w5h2-cell" :class="{
          'ai-filled': result.inferred.includes(f.key),
        }" :style="{'--accent': f.color}">
          <div class="cell-hd">
            <span class="cell-icon">{{ f.icon }}</span>
            <span class="cell-name">{{ f.label }}</span>
            <span class="cell-sub">· {{ f.sub }}</span>
            <el-tag v-if="result.inferred.includes(f.key)" size="small" type="warning"
              effect="light" style="margin-left:auto;">🤖 AI</el-tag>
          </div>
          <el-input v-model="form[f.key]" :placeholder="f.hint" type="textarea"
            :rows="2" resize="none" />
        </div>

        <div class="w5h2-cell w5h2-center" style="--accent: #dc2626;">
          <div class="cell-hd">
            <span class="cell-icon">❓</span>
            <span class="cell-name">Why · 根本原因</span>
            <el-tag size="small" type="danger" effect="light" style="margin-left:auto;">必填</el-tag>
          </div>
          <el-input v-model="form.why" placeholder="请输入根本原因（必填）"
            type="textarea" :rows="4" resize="none" />
        </div>

        <div v-for="f in orderBottom" :key="f.key" class="w5h2-cell" :class="{
          'ai-filled': result.inferred.includes(f.key),
        }" :style="{'--accent': f.color}">
          <div class="cell-hd">
            <span class="cell-icon">{{ f.icon }}</span>
            <span class="cell-name">{{ f.label }}</span>
            <span class="cell-sub">· {{ f.sub }}</span>
            <el-tag v-if="result.inferred.includes(f.key)" size="small" type="warning"
              effect="light" style="margin-left:auto;">🤖 AI</el-tag>
          </div>
          <el-input v-model="form[f.key]" :placeholder="f.hint" type="textarea"
            :rows="2" resize="none" />
        </div>
      </div>

      <div class="qc-actions" style="margin-top: 16px;">
        <el-button type="primary" :loading="loading" @click="run" style="flex:1;">
          <el-icon><MagicStick /></el-icon>&nbsp;
          {{ hasResult ? '重新推理' : (useLlm ? 'AI 补全空白' : '保存并展示') }}
        </el-button>
        <el-button v-if="hasResult" @click="clearAi">
          <el-icon><RefreshLeft /></el-icon>&nbsp;清空 AI 补全
        </el-button>
      </div>

      <transition name="fade">
        <div v-if="loading && useLlm" style="margin-top:12px;">
          <el-progress :percentage="Math.round(progress)" :stroke-width="6" :show-text="false" />
          <div style="text-align:center;color:#94a3b8;font-size:12px;margin-top:4px;">
            AI 推理中… <span class="mono">{{ elapsed }}s</span>
          </div>
        </div>
      </transition>
    </div>

    <transition name="fade">
      <div class="qc-panel" v-if="result.reasoning">
        <div class="qc-panel-hd">🤖 推理逻辑</div>
        <div class="summary-text">{{ result.reasoning }}</div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { analyzeW5H2, downloadPptx } from '../api'

const form = reactive({
  topic: '', why: '', what: '', where: '', when: '', who: '', how: '', how_much: '',
})
const useLlm = ref(true)
const loading = ref(false)
const result = reactive({ inferred: [], reasoning: '' })
const pptxLoading = ref(false)
const progress = ref(0); const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

const orderTop = [
  { key: 'what',  icon: '❔', label: 'What',  sub: '问题现象',  color: '#0284c7', hint: '发生了什么问题/现象' },
  { key: 'where', icon: '📍', label: 'Where', sub: '地点/环节', color: '#059669', hint: '发生的地点、工序、机台' },
  { key: 'who',   icon: '👤', label: 'Who',   sub: '责任人',    color: '#7c3aed', hint: '责任人、参与人、岗位' },
]
const orderBottom = [
  { key: 'when',     icon: '⏰', label: 'When',     sub: '时间节点', color: '#db2777', hint: '发生时间 / 改善期限' },
  { key: 'how',      icon: '🛠', label: 'How',      sub: '对策/措施', color: '#0891b2', hint: '具体对策、方案、步骤' },
  { key: 'how_much', icon: '💰', label: 'How Much', sub: '成本/目标', color: '#f59e0b', hint: '预算、目标、KPI' },
]

const hasResult = computed(() =>
  Object.values(form).some(v => v?.trim()) && (result.inferred.length || form.why.trim())
)

function loadSample() {
  Object.assign(form, {
    topic: '焊接工序不良率偏高',
    why: '焊工技能参差不齐，作业标准执行不到位',
    what: '', where: '', when: '', who: '', how: '', how_much: '',
  })
}

function startProgress() {
  progress.value = 0; elapsed.value = 0
  progressTimer = setInterval(() => {
    if (progress.value < 88)
      progress.value = Math.min(88, progress.value + Math.max(0.3, (88 - progress.value) * 0.015))
  }, 600)
  elapsedTimer = setInterval(() => { elapsed.value += 1 }, 1000)
}
function stopProgress() {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
  progressTimer = elapsedTimer = null
  progress.value = 100
}

async function run() {
  if (!form.topic?.trim()) return ElMessage.warning('请填写主题')
  if (!form.why?.trim() || form.why.trim().length < 2)
    return ElMessage.error('Why（根本原因）为必填字段')

  loading.value = true
  if (useLlm.value) startProgress()
  try {
    const resp = await analyzeW5H2({ ...form, use_llm: useLlm.value })
    // 回填 AI 补全的字段（用户已填的保留）
    for (const f of resp.inferred) {
      if (!form[f]?.trim()) form[f] = resp[f]
    }
    result.inferred = resp.inferred
    result.reasoning = resp.reasoning
    if (useLlm.value) stopProgress()
    const n = resp.inferred.length
    ElMessage.success(n ? `AI 补全 ${n} 项` : '保存完成')
  } catch (e) {
    stopProgress()
    ElMessage.error(e.response?.data?.detail || e.message || '失败')
  } finally {
    setTimeout(() => { loading.value = false }, 300)
  }
}

function clearAi() {
  for (const f of result.inferred) form[f] = ''
  result.inferred = []
  result.reasoning = ''
  ElMessage.info('AI 补全内容已清空')
}

function exportJson() {
  const blob = new Blob([JSON.stringify({...form, ...result}, null, 2)],
                        {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `5W2H_${form.topic}.json`; a.click()
}

async function exportPptx() {
  pptxLoading.value = true
  try {
    await downloadPptx('w5h2', { ...form, ...result }, `5W2H_${form.topic}.pptx`)
    ElMessage.success('PPTX 已下载')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { pptxLoading.value = false }
}

onBeforeUnmount(() => {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
})
</script>

<style scoped>
.qc-page { padding: 4px; }
.qc-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; padding: 14px 18px; border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04); margin-bottom: 12px;
  border: 1px solid #eef2f7;
}
.tb-left { display: flex; align-items: center; gap: 12px; }
.tb-title { font-size: 16px; font-weight: 600; color: #0f172a; }
.tb-sub { font-size: 12px; color: #64748b; margin-top: 2px; }
.tb-right { display: flex; gap: 8px; }

.qc-panel {
  background: #fff; border-radius: 10px; padding: 16px 18px;
  margin-bottom: 12px; border: 1px solid #eef2f7;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.qc-panel-hd {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 600; color: #334155;
  margin-bottom: 12px;
}

.w5h2-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 10px;
}
.w5h2-cell {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px 12px;
  border-left: 3px solid var(--accent);
  transition: all .2s;
}
.w5h2-cell.ai-filled {
  background: #fffbeb;
  border-left-color: #f59e0b;
  box-shadow: 0 0 0 1px #fef3c7;
}
.w5h2-cell.w5h2-center {
  grid-column: 2;
  grid-row: 1 / span 2;
  background: #fef2f2;
  border: 2px solid #dc2626;
  border-left-width: 4px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
}
.w5h2-cell.w5h2-center :deep(.el-textarea__inner) {
  font-weight: 500;
  border-color: #fecaca;
}
.cell-hd {
  display: flex; align-items: center; gap: 4px;
  font-size: 12.5px; margin-bottom: 6px;
}
.cell-icon { font-size: 15px; }
.cell-name { font-weight: 600; color: var(--accent); }
.cell-sub { color: #94a3b8; font-size: 11.5px; }

.qc-form :deep(.el-form-item) { margin-bottom: 12px; }
.qc-form :deep(.el-form-item__label) { padding-bottom: 4px; font-size: 12px; color: #475569; }
.qc-actions { display: flex; gap: 8px; }
.summary-text {
  color: #451a03; line-height: 1.75; font-size: 13px;
  background: #fffbeb; padding: 12px 14px; border-radius: 6px;
  border-left: 3px solid #f59e0b;
}
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; }
.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#dc2626"><Grid /></el-icon>
        <div>
          <div class="tb-title">5W2H 分析（5W2H Analysis）</div>
          <div class="tb-sub">批量根因分析：每行一条 Why (必填)，其余字段可让 AI 联想补全</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button size="default" :disabled="!hasResult" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button size="default" :disabled="!hasResult"
          :loading="xlsxLoading" @click="exportXlsx">
          <el-icon><Grid /></el-icon>&nbsp;XLSX
        </el-button>
        <el-button size="default" :disabled="!hasResult"
          :loading="pptxLoading" @click="exportPptx">
          <el-icon><Document /></el-icon>&nbsp;PPTX
        </el-button>
      </div>
    </div>

    <div class="qc-panel">
      <div class="qc-panel-hd">
        <span>📝 主题与选项</span>
        <div style="display:flex;gap:8px;align-items:center;">
          <el-checkbox v-model="useLlm" size="small">未填字段用 AI 补全</el-checkbox>
        </div>
      </div>
      <ToolkitBar :toolkit="toolkit" />
      <el-form label-position="top" size="default">
        <el-form-item label="主题">
          <el-input v-model="topic" placeholder="如：焊接工序不良率偏高" />
        </el-form-item>
        <el-form-item label="背景（可选）">
          <el-input v-model="context" type="textarea" :rows="2" resize="none"
            placeholder="行业/场景/关注点" />
        </el-form-item>
      </el-form>
    </div>

    <div class="qc-panel">
      <div class="qc-panel-hd">
        <span>📋 5W2H 表格（{{ rows.length }} 行）</span>
        <div style="display:flex;gap:6px;">
          <el-button size="small" @click="showPaste = true">
            <el-icon><CopyDocument /></el-icon>&nbsp;Excel 粘贴
          </el-button>
          <el-button size="small" @click="loadSample">
            <el-icon><Files /></el-icon>&nbsp;示例
          </el-button>
          <el-button size="small" @click="addRow">
            <el-icon><Plus /></el-icon>&nbsp;新增行
          </el-button>
        </div>
      </div>

      <div class="tip-bar">
        💡 只需填 <strong>Why（根本原因）</strong>，勾选 AI 补全后其他 6 列会自动推理。可直接从 Excel 复制粘贴。
      </div>

      <div class="table-wrap">
        <table class="w5h2-table">
          <thead>
            <tr>
              <th style="width:36px;">#</th>
              <th class="col-why" style="width:180px;">根因 (Why) <span class="req">*</span></th>
              <th style="width:150px;">对象 (What)</th>
              <th style="width:120px;">地点 (Where)</th>
              <th style="width:100px;">时间 (When)</th>
              <th style="width:100px;">责任人 (Who)</th>
              <th style="width:180px;">方法 (How)</th>
              <th style="width:120px;">程度 (How Much)</th>
              <th style="width:36px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in rows" :key="i">
              <td class="idx">{{ i + 1 }}</td>
              <td v-for="f in cols" :key="f"
                  :class="{
                    'why-cell': f === 'why',
                    'ai-cell': isAi(i, f),
                  }">
                <el-input v-model="r[f]" size="small" type="textarea" :rows="2"
                  resize="none"
                  :placeholder="f === 'why' ? '根本原因（必填）' : ''" />
                <span v-if="isAi(i, f)" class="ai-badge">🤖 AI</span>
              </td>
              <td>
                <el-button text size="small" @click="removeRow(i)"
                  :disabled="rows.length === 1">
                  <el-icon><Close /></el-icon>
                </el-button>
              </td>
            </tr>
          </tbody>
        </table>
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
      <div class="qc-panel" v-if="reasoning">
        <div class="qc-panel-hd">🤖 推理逻辑</div>
        <div class="summary-text">{{ reasoning }}</div>
      </div>
    </transition>

    <div v-if="hasResult">
      <NextStepBar :from="'w5h2'" :topic="topic || ''" />
    </div>

    <!-- Excel 粘贴对话框 -->
    <el-dialog v-model="showPaste" title="从 Excel 粘贴" width="640px">
      <div style="color:#64748b;font-size:12px;margin-bottom:8px;">
        直接从 Excel 复制表格粘贴到下方。第一列必须是 <strong>Why (根因)</strong>。
        列顺序：<code>Why | What | Where | When | Who | How | HowMuch</code>，缺列的用制表符空占位。
        <br>可含表头行（自动跳过）。
      </div>
      <el-input v-model="pasteText" type="textarea" :rows="10"
        placeholder="从 Excel 复制粘贴到这里…" resize="none" />
      <template #footer>
        <el-button @click="showPaste = false">取消</el-button>
        <el-button type="primary" @click="applyPaste">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { analyzeW5H2, downloadPptx, downloadXlsx } from '../api'
import { tryAttachToProject } from '../composables/useAttach'
import ToolkitBar from '../components/ToolkitBar.vue'
import NextStepBar from '../components/NextStepBar.vue'
import { useToolkit } from '../composables/useToolkit'

const cols = ['why','what','where','when','who','how','how_much']

const topic = ref('')
const context = ref('')
const useLlm = ref(true)
const rows = reactive([blankRow()])
const inferredMap = reactive({})  // rowIdx -> Set<field>
const reasoning = ref('')

const loading = ref(false)
const pptxLoading = ref(false)
const xlsxLoading = ref(false)
const showPaste = ref(false)
const pasteText = ref('')

const progress = ref(0); const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

// —— 示例数据 & 历史记录 —— //
const form = reactive({ topic: '', context: '' })
watch(form, () => {
  if (form.topic !== undefined) topic.value = form.topic
  if (form.context !== undefined) context.value = form.context
}, { deep: true })
const toolkit = useToolkit('w5h2', form)

function blankRow() {
  return { why:'', what:'', where:'', when:'', who:'', how:'', how_much:'' }
}
function addRow() { rows.push(blankRow()) }
function removeRow(i) {
  rows.splice(i, 1)
  delete inferredMap[i]
  // 重新排 inferredMap 键
  const remap = {}
  Object.keys(inferredMap).sort((a,b)=>+a-+b).forEach((k,newIdx) => {
    if (+k !== i) remap[newIdx] = inferredMap[k]
  })
  Object.keys(inferredMap).forEach(k => delete inferredMap[k])
  Object.assign(inferredMap, remap)
}

function isAi(i, f) {
  return inferredMap[i]?.has(f) ?? false
}

function loadSample() {
  topic.value = '焊接工序不良率偏高'
  context.value = '3 号机台近 2 周不良率从 1.2% 升至 3.5%'
  rows.splice(0, rows.length,
    { why:'焊工技能参差不齐，作业标准执行不到位',
      what:'', where:'', when:'', who:'', how:'', how_much:'' },
    { why:'焊丝供应商更换后规格波动',
      what:'', where:'', when:'', who:'', how:'', how_much:'' },
    { why:'保护气流量表读数不准',
      what:'', where:'', when:'', who:'', how:'', how_much:'' },
  )
  Object.keys(inferredMap).forEach(k => delete inferredMap[k])
  reasoning.value = ''
}

function applyPaste() {
  const lines = pasteText.value.split(/\r?\n/).map(l => l.trim()).filter(Boolean)
  if (!lines.length) return ElMessage.warning('内容为空')
  // 跳过明显的表头行（首格含 why/根因/why?）
  const firstCells = lines[0].split(/\t/).map(c => c.toLowerCase())
  const skipHead = /why|根因|根本原因/.test(firstCells[0])
  const raw = skipHead ? lines.slice(1) : lines
  const parsed = raw.map(line => {
    const cells = line.split(/\t/)
    return {
      why: (cells[0] || '').trim(),
      what: (cells[1] || '').trim(),
      where: (cells[2] || '').trim(),
      when: (cells[3] || '').trim(),
      who: (cells[4] || '').trim(),
      how: (cells[5] || '').trim(),
      how_much: (cells[6] || '').trim(),
    }
  }).filter(r => r.why.length >= 2)
  if (!parsed.length) return ElMessage.error('未识别到有效行（Why 必须至少 2 字符）')
  rows.splice(0, rows.length, ...parsed)
  Object.keys(inferredMap).forEach(k => delete inferredMap[k])
  showPaste.value = false
  pasteText.value = ''
  ElMessage.success(`导入 ${parsed.length} 行`)
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

const hasResult = computed(() =>
  Object.keys(inferredMap).length > 0 ||
  rows.some(r => cols.some(f => r[f]?.trim()))
)

async function run() {
  if (!topic.value.trim()) return ElMessage.warning('请填写主题')
  const valid = rows.filter(r => r.why?.trim().length >= 2)
  if (!valid.length) return ElMessage.error('至少 1 行 Why（根本原因）为必填')

  loading.value = true
  if (useLlm.value) startProgress()
  try {
    const resp = await analyzeW5H2({
      topic: topic.value,
      context: context.value,
      use_llm: useLlm.value,
      rows: valid.map(r => ({...r})),
    })
    // 回填：仅 AI 补全过的字段（后端已过滤，用户填的原样返回）
    // 注意：valid 可能少于 rows（跳过了 why 空行），按 valid 顺序回填
    let vi = 0
    for (let i = 0; i < rows.length; i++) {
      if (!rows[i].why?.trim() || rows[i].why.trim().length < 2) continue
      const rr = resp.rows[vi++]
      if (!rr) break
      for (const f of rr.inferred) {
        if (!rows[i][f]?.trim()) rows[i][f] = rr[f]
      }
      if (rr.inferred.length) inferredMap[i] = new Set(rr.inferred)
      else delete inferredMap[i]
    }
    reasoning.value = resp.reasoning || ''
    toolkit.saveHistory(resp, { topic: topic.value, context: context.value })
    await tryAttachToProject('w5h2', { topic: topic.value, context: context.value }, resp)
    if (useLlm.value) stopProgress()
    const total = Object.values(inferredMap).reduce((a, s) => a + s.size, 0)
    ElMessage.success(total ? `AI 补全 ${total} 个字段` : '保存完成')
  } catch (e) {
    stopProgress()
    ElMessage.error(e.response?.data?.detail || e.message || '失败')
  } finally {
    setTimeout(() => { loading.value = false }, 300)
  }
}

function clearAi() {
  for (const [i, fs] of Object.entries(inferredMap)) {
    for (const f of fs) if (rows[+i]) rows[+i][f] = ''
  }
  Object.keys(inferredMap).forEach(k => delete inferredMap[k])
  reasoning.value = ''
  ElMessage.info('AI 补全内容已清空')
}

function buildResultPayload() {
  return {
    topic: topic.value,
    reasoning: reasoning.value,
    rows: rows
      .filter(r => r.why?.trim())
      .map((r, i) => ({
        ...r,
        inferred: [...(inferredMap[rows.indexOf(r)] || new Set())],
      })),
  }
}

function exportJson() {
  const blob = new Blob([JSON.stringify(buildResultPayload(), null, 2)],
                        {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `5W2H_${topic.value}.json`; a.click()
}

async function exportPptx() {
  pptxLoading.value = true
  try {
    await downloadPptx('w5h2', buildResultPayload(), `5W2H_${topic.value}.pptx`)
    ElMessage.success('PPTX 已下载')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { pptxLoading.value = false }
}

async function exportXlsx() {
  xlsxLoading.value = true
  try {
    await downloadXlsx('w5h2', buildResultPayload(), `5W2H_${topic.value}.xlsx`)
    ElMessage.success('XLSX 已下载（按当前品牌主题配色）')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { xlsxLoading.value = false }
}

onBeforeUnmount(() => {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
})

// 从 URL query 自动填入 topic (工具间跳转时透传)
const route = useRoute()
onMounted(() => {
  const q = route.query.topic
  if (q && !topic.value) {
    topic.value = String(q)
    form.topic = topic.value
    ElMessage.info('已带入上一步的主题')
  }
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
.tip-bar {
  background: #eff6ff; color: #1e40af; padding: 8px 12px;
  border-radius: 6px; font-size: 12.5px; margin-bottom: 10px;
  border-left: 3px solid #3b82f6;
}
.qc-actions { display: flex; gap: 8px; }

.table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 8px; }
.w5h2-table {
  border-collapse: collapse; width: 100%; font-size: 12.5px;
  table-layout: fixed;
}
.w5h2-table thead th {
  background: #0f172a; color: #fff; padding: 8px 6px;
  font-weight: 600; text-align: left; white-space: nowrap;
}
.w5h2-table thead th.col-why { background: #991b1b; }
.w5h2-table thead th .req { color: #fca5a5; }
.w5h2-table tbody td {
  padding: 4px; vertical-align: top;
  border-top: 1px solid #f1f5f9; position: relative;
}
.w5h2-table td.idx {
  text-align: center; font-weight: 600; color: #64748b;
  background: #f8fafc; font-size: 13px;
}
.w5h2-table td.why-cell { background: #fef2f2; }
.w5h2-table td.why-cell :deep(.el-textarea__inner) {
  border-color: #fecaca; font-weight: 500;
}
.w5h2-table td.ai-cell { background: #fffbeb; }
.w5h2-table td.ai-cell :deep(.el-textarea__inner) {
  border-color: #fde68a; background: #fffef6;
}
.ai-badge {
  position: absolute; top: 2px; right: 6px;
  font-size: 9px; color: #b45309; background: #fef3c7;
  padding: 1px 4px; border-radius: 3px; font-weight: 600;
}
.w5h2-table :deep(.el-textarea__inner) {
  padding: 4px 6px; font-size: 12px; min-height: 32px;
}

.summary-text {
  color: #451a03; line-height: 1.75; font-size: 13px;
  background: #fffbeb; padding: 12px 14px; border-radius: 6px;
  border-left: 3px solid #f59e0b;
}
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; }
.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

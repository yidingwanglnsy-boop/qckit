<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#7c3aed"><Search /></el-icon>
        <div>
          <div class="tb-title">根因确认（Root Cause Analysis）</div>
          <div class="tb-sub">要因确认表：症结 → 末端原因（1:N）；空缺字段可让 AI 联想补全</div>
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
      <el-form label-position="top" size="default">
        <el-form-item label="主题">
          <el-input v-model="topic" placeholder="如：焊接工序不良率偏高的要因确认" />
        </el-form-item>
        <el-form-item label="背景（可选）">
          <el-input v-model="context" type="textarea" :rows="2" resize="none"
            placeholder="行业/场景/关注点" />
        </el-form-item>
      </el-form>
    </div>

    <div class="qc-panel">
      <div class="qc-panel-hd">
        <span>📋 要因确认表（{{ rows.length }} 行）</span>
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
        💡 <strong>症结</strong> 与 <strong>末端原因</strong> 必填（1:N，同一症结重复填即可）；勾选 AI 补全后
        <strong>确认内容 / 确认方法 / 确认结果 / 是否要因</strong> 会自动推理。责任人、完成时间由人工填写。
      </div>

      <div class="table-wrap">
        <table class="rca-table">
          <thead>
            <tr>
              <th style="width:36px;">#</th>
              <th class="col-key" style="width:170px;">症结 (Symptom) <span class="req">*</span></th>
              <th class="col-key2" style="width:180px;">末端原因 (Root Cause) <span class="req">*</span></th>
              <th style="width:200px;">确认内容 (Content)</th>
              <th style="width:150px;">确认方法 (Method)</th>
              <th style="width:200px;">确认结果 (Result)</th>
              <th style="width:100px;">责任人 (Owner)</th>
              <th style="width:110px;">完成时间 (Due)</th>
              <th style="width:90px;">是否要因 (Key?)</th>
              <th style="width:36px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in rows" :key="i" :class="{'group-band': groupBand(i)}">
              <td class="idx">{{ i + 1 }}</td>
              <td class="sym-cell">
                <el-input v-model="r.symptom" size="small" type="textarea" :rows="2"
                  resize="none" placeholder="症结（必填）" />
              </td>
              <td class="cause-cell">
                <el-input v-model="r.cause" size="small" type="textarea" :rows="2"
                  resize="none" placeholder="末端原因（必填）" />
              </td>
              <td v-for="f in ['content','method','result','owner','due']" :key="f"
                  :class="{ 'ai-cell': isAi(i, f) }">
                <el-input v-model="r[f]" size="small" type="textarea" :rows="2"
                  resize="none" />
                <span v-if="isAi(i, f)" class="ai-badge">🤖 AI</span>
              </td>
              <td :class="keyCellClass(r, i)">
                <el-select v-model="r.is_key" size="small" placeholder="—" clearable style="width:100%;">
                  <el-option label="是" value="是" />
                  <el-option label="否" value="否" />
                  <el-option label="待验证" value="待验证" />
                </el-select>
                <span v-if="isAi(i, 'is_key')" class="ai-badge">🤖</span>
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

    <el-dialog v-model="showPaste" title="从 Excel 粘贴" width="720px">
      <div style="color:#64748b;font-size:12px;margin-bottom:8px;">
        列顺序（用 Tab 分隔）：<code>症结 | 末端原因 | 确认内容 | 确认方法 | 确认结果 | 责任人 | 完成时间 | 是否要因</code><br>
        <strong>症结、末端原因</strong> 必填；同一症结的多条末端原因，症结列可留空（会向上继承）或重复填写。
        含表头行自动跳过。
      </div>
      <el-input v-model="pasteText" type="textarea" :rows="12"
        placeholder="从 Excel 复制粘贴到这里…" resize="none" />
      <template #footer>
        <el-button @click="showPaste = false">取消</el-button>
        <el-button type="primary" @click="applyPaste">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { analyzeRca, downloadPptx, downloadXlsx } from '../api'

const AI_FIELDS = ['content','method','result','is_key']
const ALL_FIELDS = ['content','method','result','owner','due','is_key']

const topic = ref('')
const context = ref('')
const useLlm = ref(true)
const rows = reactive([blankRow()])
const inferredMap = reactive({})
const reasoning = ref('')

const loading = ref(false)
const pptxLoading = ref(false)
const xlsxLoading = ref(false)
const showPaste = ref(false)
const pasteText = ref('')

const progress = ref(0); const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

function blankRow() {
  return { symptom:'', cause:'', content:'', method:'', result:'', owner:'', due:'', is_key:'' }
}
function addRow() { rows.push(blankRow()) }
function removeRow(i) {
  rows.splice(i, 1)
  delete inferredMap[i]
  const remap = {}
  Object.keys(inferredMap).sort((a,b)=>+a-+b).forEach((k,newIdx) => {
    if (+k !== i) remap[newIdx] = inferredMap[k]
  })
  Object.keys(inferredMap).forEach(k => delete inferredMap[k])
  Object.assign(inferredMap, remap)
}

function isAi(i, f) { return inferredMap[i]?.has(f) ?? false }

// 同一 symptom 连续行浅底交替；用累计切换次数的奇偶决定
function groupBand(i) {
  let toggle = 0, prev = null
  for (let k = 0; k <= i; k++) {
    if (rows[k].symptom !== prev) { toggle++; prev = rows[k].symptom }
  }
  return toggle % 2 === 0
}

function keyCellClass(r, i) {
  const v = (r.is_key || '').trim()
  if (v === '是') return 'key-yes'
  if (v === '否') return 'key-no'
  if (isAi(i, 'is_key')) return 'ai-cell'
  return ''
}

function loadSample() {
  topic.value = '焊接工序不良率偏高的要因确认'
  context.value = '3 号机台近 2 周不良率从 1.2% 升至 3.5%'
  rows.splice(0, rows.length,
    { symptom:'焊缝气孔率上升', cause:'保护气流量表读数偏差', content:'', method:'', result:'', owner:'', due:'', is_key:'' },
    { symptom:'焊缝气孔率上升', cause:'焊工作业标准执行不到位',  content:'', method:'', result:'', owner:'', due:'', is_key:'' },
    { symptom:'焊丝送丝不稳', cause:'新批次焊丝直径公差偏大',   content:'', method:'', result:'', owner:'', due:'', is_key:'' },
  )
  Object.keys(inferredMap).forEach(k => delete inferredMap[k])
  reasoning.value = ''
}

function applyPaste() {
  const lines = pasteText.value.split(/\r?\n/).map(l => l.trimEnd()).filter(l => l.trim())
  if (!lines.length) return ElMessage.warning('内容为空')
  const first = lines[0].split(/\t/).map(c => c.toLowerCase())
  const skipHead = /症结|symptom/.test(first[0])
  const raw = skipHead ? lines.slice(1) : lines

  let carrySym = ''
  const parsed = raw.map(line => {
    const c = line.split(/\t/)
    const sym = (c[0] || '').trim() || carrySym  // 空则继承上一行症结
    if (sym) carrySym = sym
    return {
      symptom: sym,
      cause:   (c[1] || '').trim(),
      content: (c[2] || '').trim(),
      method:  (c[3] || '').trim(),
      result:  (c[4] || '').trim(),
      owner:   (c[5] || '').trim(),
      due:     (c[6] || '').trim(),
      is_key:  (c[7] || '').trim(),
    }
  }).filter(r => r.symptom.length >= 2 && r.cause.length >= 2)

  if (!parsed.length) return ElMessage.error('未识别到有效行（症结、末端原因至少 2 字符）')
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
  rows.some(r => ALL_FIELDS.some(f => r[f]?.trim()) || r.symptom?.trim() || r.cause?.trim())
)

async function run() {
  if (!topic.value.trim()) return ElMessage.warning('请填写主题')
  const valid = rows.filter(r =>
    (r.symptom?.trim().length >= 2) && (r.cause?.trim().length >= 2))
  if (!valid.length) return ElMessage.error('至少 1 行的 症结 与 末端原因 都需 ≥ 2 字符')

  loading.value = true
  if (useLlm.value) startProgress()
  try {
    const resp = await analyzeRca({
      topic: topic.value,
      context: context.value,
      use_llm: useLlm.value,
      rows: valid.map(r => ({...r})),
    })
    let vi = 0
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i]
      if (!(r.symptom?.trim().length >= 2 && r.cause?.trim().length >= 2)) continue
      const rr = resp.rows[vi++]
      if (!rr) break
      for (const f of rr.inferred) {
        if (!rows[i][f]?.trim()) rows[i][f] = rr[f]
      }
      if (rr.inferred.length) inferredMap[i] = new Set(rr.inferred)
      else delete inferredMap[i]
    }
    reasoning.value = resp.reasoning || ''
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
      .filter(r => r.symptom?.trim() && r.cause?.trim())
      .map((r) => ({
        ...r,
        inferred: [...(inferredMap[rows.indexOf(r)] || new Set())],
      })),
  }
}

function exportJson() {
  const blob = new Blob([JSON.stringify(buildResultPayload(), null, 2)],
                        {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `根因确认_${topic.value}.json`; a.click()
}

async function exportPptx() {
  pptxLoading.value = true
  try {
    await downloadPptx('rca', buildResultPayload(), `根因确认_${topic.value}.pptx`)
    ElMessage.success('PPTX 已下载')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { pptxLoading.value = false }
}

async function exportXlsx() {
  xlsxLoading.value = true
  try {
    await downloadXlsx('rca', buildResultPayload(), `根因确认_${topic.value}.xlsx`)
    ElMessage.success('XLSX 已下载（按当前品牌主题配色）')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { xlsxLoading.value = false }
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
  font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 12px;
}
.tip-bar {
  background: #f5f3ff; color: #5b21b6; padding: 8px 12px;
  border-radius: 6px; font-size: 12.5px; margin-bottom: 10px;
  border-left: 3px solid #7c3aed;
}
.qc-actions { display: flex; gap: 8px; }

.table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 8px; }
.rca-table {
  border-collapse: collapse; width: 100%; font-size: 12.5px;
  table-layout: fixed;
}
.rca-table thead th {
  background: #0f172a; color: #fff; padding: 8px 6px;
  font-weight: 600; text-align: left; white-space: nowrap;
}
.rca-table thead th.col-key  { background: #1e3a8a; }
.rca-table thead th.col-key2 { background: #7c2d12; }
.rca-table thead th .req { color: #fca5a5; }
.rca-table tbody td {
  padding: 4px; vertical-align: top;
  border-top: 1px solid #f1f5f9; position: relative;
}
.rca-table tbody tr.group-band td.sym-cell { background: #eff6ff; }
.rca-table tbody tr:not(.group-band) td.sym-cell { background: #f8fafc; }
.rca-table td.idx {
  text-align: center; font-weight: 600; color: #64748b;
  background: #f8fafc; font-size: 13px;
}
.rca-table td.sym-cell :deep(.el-textarea__inner) {
  border-color: #bfdbfe; font-weight: 500; color: #1e3a8a;
}
.rca-table td.cause-cell { background: #fef3c7; }
.rca-table td.cause-cell :deep(.el-textarea__inner) {
  border-color: #fde68a; font-weight: 500; color: #7c2d12;
}
.rca-table td.ai-cell { background: #fffbeb; }
.rca-table td.ai-cell :deep(.el-textarea__inner),
.rca-table td.ai-cell :deep(.el-select .el-input__wrapper) {
  border-color: #fde68a; background: #fffef6;
}
.rca-table td.key-yes { background: #fee2e2; }
.rca-table td.key-yes :deep(.el-select .el-input__wrapper) {
  background: #dc2626; box-shadow: 0 0 0 1px #b91c1c inset;
}
.rca-table td.key-yes :deep(.el-input__inner) { color: #fff; font-weight: 600; }
.rca-table td.key-no  { background: #f1f5f9; }
.ai-badge {
  position: absolute; top: 2px; right: 6px;
  font-size: 9px; color: #b45309; background: #fef3c7;
  padding: 1px 4px; border-radius: 3px; font-weight: 600;
}
.rca-table :deep(.el-textarea__inner) {
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

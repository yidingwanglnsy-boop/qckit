<template>
  <div class="qc-page">
    <!-- 顶栏 -->
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#059669"><Collection /></el-icon>
        <div>
          <div class="tb-title">亲和图（Affinity Diagram / KJ）</div>
          <div class="tb-sub">把零散观点自动聚类成有意义的主题，支持手工调整</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button size="default" :disabled="!groups.length" @click="addGroup">
          <el-icon><Plus /></el-icon>&nbsp;新增分组
        </el-button>
        <el-button size="default" :disabled="!groups.length" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button size="default" :disabled="!groups.length" :loading="pptxLoading" @click="exportPptx">
          <el-icon><Document /></el-icon>&nbsp;PPTX
        </el-button>
        <el-button size="default" type="primary" :disabled="!groups.length" @click="exportPng">
          <el-icon><Picture /></el-icon>&nbsp;导出 PNG
        </el-button>
      </div>
    </div>

    <el-row :gutter="14">
      <!-- 左：输入 -->
      <el-col :md="7" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">📝 输入</div>
          <ToolkitBar :toolkit="toolkit" />
          <el-form label-position="top" size="default" class="qc-form">
            <el-form-item label="主题 / 情境">
              <el-input v-model="topic" placeholder="如：车间班组会议改善提案" />
            </el-form-item>
            <el-form-item>
              <template #label>
                <span>零散条目</span>
                <span style="color:#9ca3af;font-size:12px;margin-left:6px;">
                  每行一条 · {{ itemCount }} 条
                </span>
              </template>
              <el-input v-model="itemsText" type="textarea" :rows="10" resize="none"
                placeholder="师傅带徒弟没标准&#10;新员工培训时间短&#10;老员工不愿意教&#10;考核不看质量指标&#10;工资和产量挂钩&#10;返工不计入个人考核" />
            </el-form-item>
            <el-form-item label="期望分组数（可选）">
              <el-input-number v-model="targetGroups" :min="2" :max="12" size="default"
                :placeholder="'自动'" style="width:100%;" />
            </el-form-item>
            <el-form-item label="补充背景（可选）">
              <el-input v-model="context" type="textarea" :rows="2" resize="none"
                placeholder="行业/场景/关注点" />
            </el-form-item>
            <div class="qc-actions">
              <el-button type="primary" :loading="loading" @click="run" style="flex:1;">
                <el-icon><MagicStick /></el-icon>&nbsp;{{ groups.length ? '重新分析' : '开始分析' }}
              </el-button>
              <el-button @click="loadSample" :disabled="loading">
                <el-icon><Files /></el-icon>&nbsp;示例
              </el-button>
            </div>
            <el-alert v-if="groups.length" type="warning" :closable="false"
              style="margin-top:10px;" show-icon
              title="重新分析将丢失手工调整" />
          </el-form>
        </div>

        <!-- 进度 -->
        <transition name="fade">
        <div class="qc-panel" v-if="loading">
          <div class="qc-panel-hd">
            <span>⏳ 分析进度</span>
            <span class="mono">{{ elapsed }}s</span>
          </div>
          <el-progress :percentage="Math.round(progress)" :stroke-width="8" :show-text="false" />
          <ul class="stage-list">
            <li v-for="(s,i) in stages" :key="i"
                :class="i < stageIdx ? 'done' : i === stageIdx ? 'active' : ''">
              <span class="dot">{{ i < stageIdx ? '✓' : i === stageIdx ? '●' : '○' }}</span>
              <span>{{ s }}</span>
            </li>
          </ul>
        </div>
        </transition>

        <!-- 洞察 -->
        <transition name="fade">
        <div class="qc-panel" v-if="insights">
          <div class="qc-panel-hd">💡 整体洞察</div>
          <div class="summary-text">{{ insights }}</div>
          <div v-if="recommendations.length" class="rec-title">改善建议</div>
          <ol v-if="recommendations.length" class="rec-list">
            <li v-for="(r,i) in recommendations" :key="i">{{ r }}</li>
          </ol>
        </div>
        </transition>

        <!-- 未分类池 -->
        <div class="qc-panel" v-if="groups.length">
          <div class="qc-panel-hd">
            <span>📥 未分类池</span>
            <span class="mono">{{ pool.length }}</span>
          </div>
          <div class="pool" @dragover.prevent @drop="onDropToPool">
            <div v-for="(it, i) in pool" :key="'pool-'+i"
                 class="chip pool-chip" draggable="true"
                 @dragstart="onDragStart(it, '__pool__')">
              {{ it }}
            </div>
            <div v-if="!pool.length" class="pool-empty">拖入条目暂存于此</div>
          </div>
          <div style="margin-top:8px;">
            <el-input v-model="newItemText" size="small" placeholder="+ 手动添加条目"
              @keyup.enter="addPoolItem">
              <template #append>
                <el-button @click="addPoolItem">添加</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-col>

      <!-- 右：看板 -->
      <el-col :md="17" :xs="24">
        <div class="qc-panel qc-board-panel" ref="boardEl">
          <div class="qc-panel-hd">
            <span>🗂 主题看板</span>
            <span v-if="groups.length" class="topic-chip">{{ topic }} · {{ groups.length }} 组 / {{ classifiedCount }} 条</span>
          </div>

          <div v-if="!groups.length && !loading" class="board-empty">
            <el-icon :size="48" color="#cbd5e1"><Collection /></el-icon>
            <div style="margin-top:12px;color:#94a3b8;">填写左侧信息，点「开始分析」</div>
          </div>

          <div class="board" v-if="groups.length">
            <div v-for="(g, gi) in groups" :key="g.id" class="group"
                 :class="'prio-'+g.priority"
                 @dragover.prevent="onDragOver($event, g.id)"
                 @dragleave="onDragLeave"
                 @drop="onDrop($event, g.id)">
              <div class="group-hd">
                <el-input v-model="g.name" size="small" class="group-name" placeholder="主题名" />
                <el-select v-model="g.priority" size="small" class="prio-select">
                  <el-option :value="1" label="P1 高" />
                  <el-option :value="2" label="P2 中" />
                  <el-option :value="3" label="P3 低" />
                </el-select>
                <el-button size="small" text @click="removeGroup(gi)" title="删除本组">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-input v-model="g.summary" size="small" class="group-summary"
                type="textarea" :rows="2" placeholder="一句话摘要（可选）" resize="none" />
              <div class="group-body">
                <div v-for="(it, ii) in g.items" :key="g.id+'-'+ii"
                     class="chip" draggable="true"
                     @dragstart="onDragStart(it, g.id)">
                  <span class="chip-text">{{ it }}</span>
                  <el-icon class="chip-x" @click="removeItem(gi, ii)"><Close /></el-icon>
                </div>
                <div class="chip-count">{{ g.items.length }} 条</div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { analyzeAffinity, downloadPptx } from '../api'
import ToolkitBar from '../components/ToolkitBar.vue'
import { useToolkit } from '../composables/useToolkit'

const topic = ref('车间班组会议改善提案')
const itemsText = ref('')
const targetGroups = ref(null)
const context = ref('')
const loading = ref(false)
const boardEl = ref(null)

const groups = ref([])          // [{id,name,summary,items:[],priority}]
const pool = ref([])            // 未分类条目
const insights = ref('')
const recommendations = ref([])

// —— 示例数据 & 历史记录 —— //
const form = reactive({ topic: topic.value, context: '', raw_items: '' })
watch(form, () => {
  if (form.topic !== undefined) topic.value = form.topic
  if (form.context !== undefined) context.value = form.context
  if (form.raw_items !== undefined) itemsText.value = form.raw_items
}, { deep: true })
const toolkit = useToolkit('affinity', form)

// 进度
const stages = ['发送请求到 LLM', '模型思考并聚类（1-3 分钟）', '整理分组结果', '渲染看板']
const stageIdx = ref(0)
const progress = ref(0)
const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

const itemCount = computed(() =>
  itemsText.value.split('\n').map(s => s.trim()).filter(Boolean).length)
const classifiedCount = computed(() =>
  groups.value.reduce((n, g) => n + g.items.length, 0))
const newItemText = ref('')

// —— 交互 —— //
function loadSample() {
  topic.value = '车间班组会议改善提案'
  itemsText.value = [
    '师傅带徒弟没标准','新员工培训时间短','老员工不愿意教',
    '考核不看质量指标','工资和产量挂钩','返工不计入个人考核',
    'SOP版本混乱','贴在墙上的是旧版','换型时找不到最新参数',
    '来料尺寸波动大','供应商送货批次质量不稳',
    '设备保养流于形式','点检表照抄','故障后才修',
  ].join('\n')
  targetGroups.value = 5
  context.value = '注塑车间，员工30人，近3月客诉上升'
}

function startProgress() {
  progress.value = 0; elapsed.value = 0; stageIdx.value = 0
  setTimeout(() => { stageIdx.value = 1; progress.value = 8 }, 400)
  progressTimer = setInterval(() => {
    if (progress.value < 88)
      progress.value = Math.min(88, progress.value + Math.max(0.2, (88 - progress.value) * 0.012))
  }, 600)
  elapsedTimer = setInterval(() => { elapsed.value += 1 }, 1000)
}
function stopProgress(ok) {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
  progressTimer = elapsedTimer = null
  if (ok) { stageIdx.value = 3; progress.value = 100 }
}

async function run() {
  const items = itemsText.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (items.length < 3) return ElMessage.warning('至少输入 3 个条目')
  if (!topic.value.trim()) return ElMessage.warning('请填写主题')
  if (groups.value.length) {
    try { await ElMessageBox.confirm('将丢失当前手工调整，确定重新分析？', '提示', { type:'warning' }) }
    catch { return }
  }
  loading.value = true
  startProgress()
  try {
    const resp = await analyzeAffinity({
      topic: topic.value, items,
      target_groups: targetGroups.value || null,
      context: context.value,
    })
    stageIdx.value = 2; progress.value = 92
    // 拷贝一份可编辑对象
    groups.value = (resp.groups || []).map(g => ({
      id: g.id, name: g.name, summary: g.summary,
      items: [...g.items], priority: g.priority || 2,
    }))
    pool.value = []
    insights.value = resp.insights || ''
    recommendations.value = resp.recommendations || []
    toolkit.saveHistory(resp, { topic: topic.value, context: context.value, raw_items: itemsText.value })
    await nextTick()
    stopProgress(true)
    ElMessage.success(`分析完成，${groups.value.length} 组 / 用时 ${elapsed.value}s`)
  } catch (e) {
    stopProgress(false)
    ElMessage.error(e.response?.data?.detail || e.message || '分析失败')
  } finally {
    setTimeout(() => { loading.value = false }, 600)
  }
}

// —— 拖拽 —— //
let dragging = null   // { item, fromId }
function onDragStart(item, fromId) { dragging = { item, fromId } }
function onDragOver(e, gid) { e.currentTarget.classList.add('drop-hover') }
function onDragLeave(e)     { e.currentTarget.classList.remove('drop-hover') }
function onDrop(e, gid) {
  e.currentTarget.classList.remove('drop-hover')
  if (!dragging) return
  moveItem(dragging.item, dragging.fromId, gid)
  dragging = null
}
function onDropToPool(e) {
  if (!dragging) return
  moveItem(dragging.item, dragging.fromId, '__pool__')
  dragging = null
}
function moveItem(item, fromId, toId) {
  if (fromId === toId) return
  // 从源移除
  if (fromId === '__pool__') pool.value = pool.value.filter(x => x !== item)
  else {
    const src = groups.value.find(g => g.id === fromId)
    if (src) src.items = src.items.filter(x => x !== item)
  }
  // 加到目标
  if (toId === '__pool__') { if (!pool.value.includes(item)) pool.value.push(item) }
  else {
    const dst = groups.value.find(g => g.id === toId)
    if (dst && !dst.items.includes(item)) dst.items.push(item)
  }
}

// —— 编辑操作 —— //
function addGroup() {
  const nextId = 'g' + (Date.now() % 100000)
  groups.value.push({ id: nextId, name: '新分组', summary: '', items: [], priority: 2 })
}
async function removeGroup(gi) {
  const g = groups.value[gi]
  if (g.items.length) {
    try { await ElMessageBox.confirm(`「${g.name}」有 ${g.items.length} 条，将移到未分类池`, '删除分组', { type:'warning' }) }
    catch { return }
    pool.value.push(...g.items)
  }
  groups.value.splice(gi, 1)
}
function removeItem(gi, ii) {
  const item = groups.value[gi].items[ii]
  groups.value[gi].items.splice(ii, 1)
  pool.value.push(item)  // 不真删，退回未分类池
}
function addPoolItem() {
  const t = newItemText.value.trim()
  if (!t) return
  if (allItems().includes(t)) return ElMessage.warning('条目已存在')
  pool.value.push(t)
  newItemText.value = ''
}
function allItems() {
  return [...pool.value, ...groups.value.flatMap(g => g.items)]
}

// —— 导出 —— //
function exportJson() {
  const blob = new Blob([JSON.stringify({
    topic: topic.value, groups: groups.value, pool: pool.value,
    insights: insights.value, recommendations: recommendations.value,
  }, null, 2)], { type:'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `亲和图_${topic.value}.json`; a.click()
}
async function exportPng() {
  if (!boardEl.value) return
  ElMessage.info('请使用系统截图工具（Win+Shift+S / macOS Cmd+Shift+4）截取看板')
}

const pptxLoading = ref(false)
async function exportPptx() {
  if (!groups.value.length) return
  pptxLoading.value = true
  try {
    await downloadPptx('affinity', {
      topic: topic.value, groups: groups.value, pool: pool.value,
      insights: insights.value, recommendations: recommendations.value,
    }, `亲和图_${topic.value}.pptx`)
    ElMessage.success('PPTX 已下载')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { pptxLoading.value = false }
}

onBeforeUnmount(() => { clearInterval(progressTimer); clearInterval(elapsedTimer) })
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
.tb-sub   { font-size: 12px; color: #64748b; margin-top: 2px; }
.tb-right { display: flex; gap: 8px; }

.qc-panel {
  background: #fff; border-radius: 10px; padding: 14px 16px;
  margin-bottom: 12px; border: 1px solid #eef2f7;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.qc-panel-hd {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 600; color: #334155;
  margin-bottom: 10px; letter-spacing: .3px;
}
.qc-form :deep(.el-form-item) { margin-bottom: 12px; }
.qc-form :deep(.el-form-item__label) { padding-bottom: 4px; font-size: 12px; color: #475569; }
.qc-actions { display: flex; gap: 8px; }

.topic-chip {
  background: #ecfdf5; color: #047857; padding: 3px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 500;
}

/* 进度阶段 */
.stage-list { list-style: none; padding: 0; margin: 12px 0 0; font-size: 12.5px; }
.stage-list li { display: flex; align-items: center; gap: 8px; padding: 4px 0; color: #94a3b8; }
.stage-list li.done   { color: #10b981; }
.stage-list li.active { color: #059669; font-weight: 500; }
.stage-list .dot { width: 14px; text-align: center; }

/* 看板 */
.qc-board-panel { min-height: 400px; padding: 12px; position: relative; }
.board-empty {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  text-align: center; pointer-events: none;
}
.board {
  display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px;
  align-items: flex-start;
}
.group {
  flex: 0 0 240px; background: #f8fafc; border-radius: 10px;
  padding: 10px; border: 1px solid #e5e7eb;
  display: flex; flex-direction: column; gap: 6px;
  transition: box-shadow .15s;
}
.group.drop-hover {
  box-shadow: 0 0 0 2px #059669; background: #ecfdf5;
}
.group.prio-1 { border-top: 3px solid #dc2626; }
.group.prio-2 { border-top: 3px solid #f59e0b; }
.group.prio-3 { border-top: 3px solid #94a3b8; }

.group-hd { display: flex; gap: 6px; align-items: center; }
.group-name :deep(.el-input__wrapper) { background: #fff; font-weight: 600; }
.prio-select { width: 78px; }
.group-summary :deep(.el-textarea__inner) {
  background: #fff; font-size: 12px; color: #475569; padding: 6px 8px;
}
.group-body { display: flex; flex-direction: column; gap: 5px; min-height: 40px; }
.chip {
  background: #fff; padding: 6px 10px; border-radius: 6px;
  border: 1px solid #e2e8f0; font-size: 12.5px; color: #1e293b;
  cursor: grab; user-select: none;
  display: flex; align-items: center; justify-content: space-between; gap: 6px;
  transition: box-shadow .1s;
}
.chip:hover { box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.chip:active { cursor: grabbing; }
.chip-text { flex: 1; word-break: break-word; }
.chip-x {
  color: #cbd5e1; cursor: pointer; font-size: 14px;
}
.chip-x:hover { color: #ef4444; }
.chip-count {
  align-self: flex-end; font-size: 11px; color: #94a3b8; margin-top: 4px;
}

/* 未分类池 */
.pool {
  min-height: 60px; padding: 8px;
  background: #fafbfc; border: 1px dashed #cbd5e1; border-radius: 8px;
  display: flex; flex-wrap: wrap; gap: 6px;
}
.pool-empty { color: #cbd5e1; font-size: 12px; padding: 8px; }
.pool-chip {
  background: #fef3c7; border-color: #fde68a; color: #92400e;
  padding: 4px 10px;
}

.summary-text {
  color: #334155; line-height: 1.75; font-size: 13px;
  background: #f8fafc; padding: 10px 12px; border-radius: 6px;
  border-left: 3px solid #059669;
}
.rec-title { margin: 14px 0 4px; font-weight: 600; color: #0f172a; font-size: 13px; }
.rec-list { padding-left: 20px; color: #334155; line-height: 1.9; margin: 0; font-size: 13px; }
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; }

.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

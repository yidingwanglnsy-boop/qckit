<template>
  <div class="relations-page">
    <!-- 顶栏：主题 + 操作 -->
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#2563eb"><Share /></el-icon>
        <div>
          <div class="tb-title">关联图（Relations Diagram）</div>
          <div class="tb-sub">LLM 自动识别核心 / 关键 / 传导节点并推断因果关系</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button size="default" :disabled="!result" @click="relayout">
          <el-icon><Refresh /></el-icon>&nbsp;重新布局
        </el-button>
        <el-button size="default" :disabled="!result" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button size="default" :disabled="!result" :loading="pptxLoading" @click="exportPptx">
          <el-icon><Document /></el-icon>&nbsp;PPTX
        </el-button>
        <el-button size="default" type="primary" :disabled="!result" @click="exportPng">
          <el-icon><Picture /></el-icon>&nbsp;导出 PNG
        </el-button>
      </div>
    </div>

    <el-row :gutter="14" class="qc-body">
      <!-- 左：输入 + 状态 -->
      <el-col :md="7" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">📝 输入</div>
          <el-form label-position="top" size="default" class="qc-form">
            <el-form-item label="问题主题">
              <el-input v-model="topic" placeholder="如：产线A车间不良率高" />
            </el-form-item>
            <el-form-item>
              <template #label>
                <span>候选节点</span>
                <span style="color:#9ca3af;font-size:12px;margin-left:6px;">
                  每行一个 · 当前 {{ nodeCount }} 个
                </span>
              </template>
              <el-input
                v-model="nodesText" type="textarea" :rows="9" resize="none"
                placeholder="来料检验松&#10;工人培训不足&#10;设备老化&#10;标准作业书缺失" />
            </el-form-item>
            <el-form-item label="补充背景（可选）">
              <el-input v-model="context" type="textarea" :rows="2" resize="none"
                placeholder="行业/工艺/近期变更等背景" />
            </el-form-item>
            <div class="qc-actions">
              <el-button type="primary" :loading="loading" @click="run" style="flex:1;">
                <el-icon><MagicStick /></el-icon>&nbsp;{{ loading ? '分析中…' : '开始分析' }}
              </el-button>
              <el-button @click="loadSample" :disabled="loading">
                <el-icon><Files /></el-icon>&nbsp;示例
              </el-button>
            </div>
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

        <!-- 图例 + 统计 -->
        <transition name="fade">
        <div class="qc-panel" v-if="result">
          <div class="qc-panel-hd">🎨 图例</div>
          <div class="legend">
            <div class="legend-item" v-for="k in ['core','key','conduct','normal']" :key="k">
              <span class="legend-swatch" :style="{background: ROLE_BG[k], borderColor: ROLE_BORDER[k]}"></span>
              <span>{{ ROLE_NAME[k] }}</span>
              <span class="legend-count">{{ roleCount[k] || 0 }}</span>
            </div>
          </div>
          <el-divider style="margin:12px 0;" />
          <div class="stat-row">
            <div><span class="stat-num">{{ result.nodes.length }}</span> 节点</div>
            <div><span class="stat-num">{{ result.edges.length }}</span> 关系</div>
            <div><span class="stat-num">{{ elapsed }}</span> s</div>
          </div>
        </div>
        </transition>
      </el-col>

      <!-- 右：图 + 详情 -->
      <el-col :md="17" :xs="24">
        <div class="qc-panel qc-canvas-panel">
          <div class="qc-panel-hd">
            <span>🔗 关联图</span>
            <span v-if="result" class="topic-chip">{{ result.topic }}</span>
          </div>
          <div ref="cyEl" class="cy-canvas"></div>
          <div v-if="!result && !loading" class="cy-empty">
            <el-icon :size="48" color="#cbd5e1"><Share /></el-icon>
            <div style="margin-top:12px;color:#94a3b8;">填写左侧信息，点「开始分析」</div>
          </div>
        </div>

        <transition name="fade">
        <div class="qc-panel" v-if="result">
          <el-tabs v-model="tab">
            <el-tab-pane label="📌 整体解读 & 建议" name="summary">
              <div class="summary-text">{{ result.summary }}</div>
              <div class="rec-title">改善建议</div>
              <ol class="rec-list">
                <li v-for="(r,i) in result.recommendations" :key="i">{{ r }}</li>
              </ol>
            </el-tab-pane>
            <el-tab-pane :label="`🎯 节点详情 (${result.nodes.length})`" name="nodes">
              <el-table :data="sortedNodes" size="small" :row-class-name="rowClass">
                <el-table-column prop="id" label="#" width="50" />
                <el-table-column prop="label" label="节点" min-width="140" />
                <el-table-column label="角色" width="90">
                  <template #default="{row}">
                    <span class="role-chip" :style="{background:ROLE_BG[row.role],color:ROLE_TEXT[row.role]}">
                      {{ ROLE_NAME[row.role] }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="出/入度" width="90" align="center">
                  <template #default="{row}">
                    <span class="mono">{{ row.out_degree }} / {{ row.in_degree }}</span>
                  </template>
                </el-table-column>
                <el-table-column prop="reason" label="判定依据" show-overflow-tooltip />
              </el-table>
            </el-tab-pane>
            <el-tab-pane :label="`🔀 关系列表 (${result.edges.length})`" name="edges">
              <el-table :data="edgeRows" size="small">
                <el-table-column label="源" min-width="130">
                  <template #default="{row}">{{ labelOf(row.source) }}</template>
                </el-table-column>
                <el-table-column label="关系" width="100" align="center">
                  <template #default="{row}">
                    <span class="edge-label">{{ row.label || '→' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="目标" min-width="130">
                  <template #default="{row}">{{ labelOf(row.target) }}</template>
                </el-table-column>
                <el-table-column label="强度" width="90" align="center">
                  <template #default="{row}">
                    <el-rate :model-value="row.strength" :max="3" disabled size="small" />
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </div>
        </transition>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'
import { analyzeRelations, downloadPptx } from '../api'

cytoscape.use(fcose)

// —— 状态 —— //
const topic = ref('产线A车间不良率高')
const nodesText = ref('')
const context = ref('')
const loading = ref(false)
const result = ref(null)
const tab = ref('summary')
const cyEl = ref(null)
let cy = null

// —— 角色可视化配置（标准关联图配色：低饱和 + 明确层级） —— //
const ROLE_NAME   = { core:'核心', key:'关键', conduct:'传导', normal:'一般' }
const ROLE_BG     = { core:'#fee2e2', key:'#fef3c7', conduct:'#dbeafe', normal:'#f1f5f9' }
const ROLE_BORDER = { core:'#dc2626', key:'#d97706', conduct:'#2563eb', normal:'#94a3b8' }
const ROLE_TEXT   = { core:'#991b1b', key:'#92400e', conduct:'#1e40af', normal:'#334155' }

// —— 进度 —— //
const stages = ['发送请求到 LLM','模型思考并分析（1-3 分钟）','解析并校验结果','渲染关联图']
const stageIdx = ref(0)
const progress = ref(0)
const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

// —— 派生 —— //
const nodeCount = computed(() =>
  nodesText.value.split('\n').map(s => s.trim()).filter(Boolean).length)
const roleCount = computed(() => {
  const c = {}
  result.value?.nodes.forEach(n => c[n.role] = (c[n.role] || 0) + 1)
  return c
})
const roleOrder = { core:0, key:1, conduct:2, normal:3 }
const sortedNodes = computed(() =>
  result.value ? [...result.value.nodes].sort((a,b) => roleOrder[a.role] - roleOrder[b.role]) : [])
const edgeRows = computed(() => result.value?.edges || [])
const labelOf = (id) => result.value?.nodes.find(n => n.id === id)?.label || id
const rowClass = ({ row }) => `role-row-${row.role}`

// —— 交互 —— //
function loadSample() {
  topic.value = '产线A车间不良率高'
  nodesText.value = ['来料检验松','工人培训不足','设备老化','标准作业书缺失',
    '车间温湿度波动','班组长巡检少','换型频繁','首件确认流于形式'].join('\n')
  context.value = '注塑车间，近3月不良率从0.8%升到2.1%'
}

function startProgress() {
  progress.value = 0; elapsed.value = 0; stageIdx.value = 0
  setTimeout(() => { stageIdx.value = 1; progress.value = 8 }, 400)
  progressTimer = setInterval(() => {
    if (progress.value < 88) {
      progress.value = Math.min(88, progress.value + Math.max(0.2, (88 - progress.value) * 0.012))
    }
  }, 600)
  elapsedTimer = setInterval(() => { elapsed.value += 1 }, 1000)
}
function stopProgress(ok) {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
  progressTimer = elapsedTimer = null
  if (ok) { stageIdx.value = 3; progress.value = 100 }
}

async function run() {
  const nodes = nodesText.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (nodes.length < 2) return ElMessage.warning('至少输入 2 个节点')
  if (!topic.value.trim()) return ElMessage.warning('请填写问题主题')
  loading.value = true; result.value = null; tab.value = 'summary'
  startProgress()
  try {
    const resp = await analyzeRelations({ topic: topic.value, nodes, context: context.value })
    stageIdx.value = 2; progress.value = 92
    result.value = resp
    await nextTick()
    render()
    stopProgress(true)
    ElMessage.success(`分析完成，用时 ${elapsed.value}s`)
  } catch (e) {
    stopProgress(false)
    ElMessage.error(e.response?.data?.detail || e.message || '分析失败')
  } finally {
    setTimeout(() => { loading.value = false }, 600)
  }
}

// —— Cytoscape 渲染（标准关联图外观） —— //
function render() {
  const r = result.value
  const els = [
    ...r.nodes.map(n => ({
      data: { id: n.id, label: n.label, role: n.role,
              bg: ROLE_BG[n.role], border: ROLE_BORDER[n.role], text: ROLE_TEXT[n.role],
              w: Math.max(90, n.label.length * 16 + 24) }
    })),
    ...r.edges.map((e, i) => ({
      data: { id:'e'+i, source:e.source, target:e.target, label:e.label || '',
              width: e.strength, style: e.strength === 1 ? 'dashed' : 'solid' }
    }))
  ]
  if (cy) cy.destroy()
  cy = cytoscape({
    container: cyEl.value,
    elements: els,
    wheelSensitivity: 0.25,
    style: [
      { selector: 'node', style: {
          'shape': 'round-rectangle',
          'background-color': 'data(bg)',
          'border-color': 'data(border)', 'border-width': 1.5,
          'label': 'data(label)',
          'color': 'data(text)', 'font-size': 13, 'font-weight': 500,
          'text-valign': 'center', 'text-halign': 'center',
          'text-wrap': 'wrap', 'text-max-width': 140,
          'width': 'data(w)', 'height': 36,
          'padding': '10px',
      }},
      { selector: 'node[role="core"]', style: {
          'border-width': 2.5, 'font-weight': 700, 'font-size': 14,
          'height': 42,
      }},
      { selector: 'node[role="key"]', style: {
          'border-width': 2, 'font-weight': 600,
      }},
      { selector: 'edge', style: {
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#94a3b8',
          'line-color': '#94a3b8',
          'line-style': 'data(style)',
          'width': 'data(width)',
          'arrow-scale': 1.1,
          'label': 'data(label)',
          'font-size': 10, 'color': '#475569',
          'text-background-color': '#ffffff',
          'text-background-opacity': 1,
          'text-background-padding': 3,
          'text-background-shape': 'round-rectangle',
          'text-border-color': '#e2e8f0',
          'text-border-width': 1,
          'text-border-opacity': 1,
          'text-rotation': 'autorotate',
      }},
      { selector: 'edge[width >= 3]', style: {
          'line-color': '#64748b', 'target-arrow-color': '#64748b',
      }},
      { selector: ':selected', style: {
          'border-color': '#2563eb', 'border-width': 3,
      }}
    ],
    layout: {
      name: 'fcose', animate: true, animationDuration: 500,
      nodeSeparation: 110, idealEdgeLength: 150,
      nodeRepulsion: 6000, gravity: 0.25,
      randomize: true, packComponents: true,
    }
  })
}

function relayout() { if (cy) cy.layout({ name:'fcose', animate:true, randomize:true }).run() }
function exportPng() {
  if (!cy) return
  const png = cy.png({ full:true, scale:2, bg:'#ffffff' })
  const a = document.createElement('a')
  a.href = png; a.download = `关联图_${topic.value}.png`; a.click()
}
function exportJson() {
  const blob = new Blob([JSON.stringify(result.value, null, 2)], {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `关联图_${topic.value}.json`; a.click()
}

const pptxLoading = ref(false)
async function exportPptx() {
  if (!result.value) return
  pptxLoading.value = true
  try {
    await downloadPptx('relations', result.value, `关联图_${topic.value}.pptx`)
    ElMessage.success('PPTX 已下载')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { pptxLoading.value = false }
}

onBeforeUnmount(() => {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
  if (cy) cy.destroy()
})
</script>

<style scoped>
.relations-page { padding: 4px; }
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

.qc-body { margin: 0 !important; }

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

.qc-canvas-panel { padding: 12px; }
.cy-canvas {
  height: 620px;
  background: repeating-linear-gradient(0deg, #fafbfc 0px, #fafbfc 24px, #f3f4f6 24px, #f3f4f6 25px),
              repeating-linear-gradient(90deg, #fafbfc 0px, #fafbfc 24px, #f3f4f6 24px, #f3f4f6 25px);
  border-radius: 8px; border: 1px solid #e5e7eb;
}
.cy-empty {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  text-align: center; pointer-events: none;
}
.qc-canvas-panel { position: relative; }
.topic-chip {
  background: #eff6ff; color: #1d4ed8; padding: 3px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 500;
}

/* 进度阶段 */
.stage-list { list-style: none; padding: 0; margin: 12px 0 0; font-size: 12.5px; }
.stage-list li { display: flex; align-items: center; gap: 8px; padding: 4px 0; color: #94a3b8; }
.stage-list li.done   { color: #10b981; }
.stage-list li.active { color: #2563eb; font-weight: 500; }
.stage-list .dot { width: 14px; text-align: center; }

/* 图例 */
.legend { display: flex; flex-wrap: wrap; gap: 8px; }
.legend-item {
  display: flex; align-items: center; gap: 6px;
  background: #f8fafc; padding: 4px 10px; border-radius: 20px; font-size: 12px;
}
.legend-swatch {
  width: 12px; height: 12px; border-radius: 3px; border: 1.5px solid;
}
.legend-count {
  background: #fff; color: #64748b; padding: 0 6px; border-radius: 8px;
  font-size: 11px; font-weight: 600;
}
.stat-row { display: flex; justify-content: space-around; font-size: 12px; color: #64748b; }
.stat-num { font-size: 20px; font-weight: 600; color: #0f172a; margin-right: 4px; }

/* 详情 */
.summary-text { color: #334155; line-height: 1.75; font-size: 13.5px;
  background: #f8fafc; padding: 12px 14px; border-radius: 6px;
  border-left: 3px solid #2563eb; }
.rec-title { margin: 16px 0 6px; font-weight: 600; color: #0f172a; font-size: 13px; }
.rec-list { padding-left: 22px; color: #334155; line-height: 1.9; margin: 0; }
.rec-list li { padding: 2px 0; }
.role-chip { padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.edge-label {
  background: #f1f5f9; color: #475569; padding: 2px 8px;
  border-radius: 4px; font-size: 12px;
}
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; }

.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

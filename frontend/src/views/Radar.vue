<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#0284c7"><Aim /></el-icon>
        <div>
          <div class="tb-title">雷达图 · Radar</div>
          <div class="tb-sub">多维度多对象对比评估，一眼看出强项与短板</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button size="default" :disabled="!result" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button size="default" :disabled="!result" :loading="pptxLoading" @click="exportPptx">
          <el-icon><Document /></el-icon>&nbsp;PPTX
        </el-button>
      </div>
    </div>

    <el-row :gutter="14">
      <el-col :md="10" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">📝 输入</div>
          <el-form label-position="top" size="default" class="qc-form">
            <el-form-item label="主题">
              <el-input v-model="topic" placeholder="如：Q3 供应商综合评估" />
            </el-form-item>
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="满分">
                  <el-input-number v-model="maxScore" :min="1" :max="100"
                    style="width:100%;" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item>
                  <template #label>
                    <span>短板阈值</span>
                    <el-tooltip content="低于此比例视为短板">
                      <el-icon style="margin-left:4px;color:#9ca3af;"><InfoFilled /></el-icon>
                    </el-tooltip>
                  </template>
                  <el-input-number v-model="weakThreshold" :min="10" :max="95" :step="5"
                    style="width:100%;">
                    <template #suffix>%</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <template #label>
                <span>维度</span>
                <span style="color:#9ca3af;font-size:12px;margin-left:6px;">
                  {{ dimensions.length }} 个（3-12）
                </span>
              </template>
              <div class="chips-edit">
                <el-tag v-for="(d,i) in dimensions" :key="i" closable
                        @close="removeDim(i)" size="default" type="info" effect="light"
                        style="margin:2px;">
                  {{ d }}
                </el-tag>
                <el-input v-model="newDim" size="small" placeholder="新维度回车"
                  style="width:130px;margin:2px;"
                  @keyup.enter="addDim" />
              </div>
            </el-form-item>

            <el-form-item>
              <template #label>
                <span>对象与打分</span>
                <span style="color:#9ca3af;font-size:12px;margin-left:6px;">
                  {{ entities.length }} 个（1-6）
                </span>
              </template>
              <div class="ent-editor">
                <div v-for="(e, i) in entities" :key="i" class="ent-block">
                  <div class="ent-hd">
                    <el-input v-model="e.name" size="small"
                      style="width: 140px;" placeholder="对象名" />
                    <span style="color:#94a3b8;font-size:12px;margin-left:8px;">
                      均分 {{ avg(e).toFixed(1) }}
                    </span>
                    <el-button text size="small" style="margin-left:auto;"
                      @click="entities.splice(i,1)"
                      :disabled="entities.length === 1">
                      <el-icon><Close /></el-icon>
                    </el-button>
                  </div>
                  <div class="score-grid">
                    <div v-for="(d,j) in dimensions" :key="j" class="score-cell">
                      <span class="score-lbl">{{ d }}</span>
                      <el-input-number v-model="e.scores[j]" size="small"
                        :min="0" :max="maxScore" :controls="false"
                        style="width:70px;" />
                    </div>
                  </div>
                </div>
                <el-button size="small" type="primary" plain @click="addEntity"
                  :disabled="entities.length >= 6" style="width:100%;">
                  <el-icon><Plus /></el-icon>&nbsp;添加对象
                </el-button>
              </div>
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="useLlm">
                <span style="font-size:13px;">调用 LLM 生成对比洞察和改善建议</span>
              </el-checkbox>
            </el-form-item>
            <el-form-item v-if="useLlm" label="背景（可选）">
              <el-input v-model="context" type="textarea" :rows="2" resize="none" />
            </el-form-item>
            <div class="qc-actions">
              <el-button type="primary" :loading="loading" @click="run" style="flex:1;">
                <el-icon><MagicStick /></el-icon>&nbsp;
                {{ result ? '重新分析' : (useLlm ? '开始分析' : '直接绘图') }}
              </el-button>
              <el-button @click="loadSample" :disabled="loading">
                <el-icon><Files /></el-icon>&nbsp;示例
              </el-button>
            </div>
          </el-form>
        </div>

        <transition name="fade">
        <div class="qc-panel" v-if="loading && useLlm">
          <div class="qc-panel-hd">
            <span>⏳ 分析进度</span><span class="mono">{{ elapsed }}s</span>
          </div>
          <el-progress :percentage="Math.round(progress)" :stroke-width="8" :show-text="false" />
        </div>
        </transition>

        <transition name="fade">
        <div class="qc-panel" v-if="result">
          <div class="qc-panel-hd">🏆 综合最强</div>
          <div class="best-chip">{{ result.best_entity }}</div>
          <div class="rec-title">各维度冠军</div>
          <div class="leaders">
            <div v-for="(who, dim) in result.dim_leaders" :key="dim" class="leader-row">
              <span class="leader-dim">{{ dim }}</span>
              <span class="leader-who">{{ who }}</span>
            </div>
          </div>
          <template v-if="result.insights">
            <div class="rec-title">💡 对比洞察</div>
            <div class="summary-text">{{ result.insights }}</div>
          </template>
          <template v-if="result.recommendations?.length">
            <div class="rec-title">改善建议</div>
            <ol class="rec-list">
              <li v-for="(r,i) in result.recommendations" :key="i">{{ r }}</li>
            </ol>
          </template>
        </div>
        </transition>
      </el-col>

      <el-col :md="14" :xs="24">
        <div class="qc-panel" style="min-height: 420px; position: relative;">
          <div class="qc-panel-hd">
            <span>📊 雷达图</span>
            <span v-if="result" class="topic-chip">
              {{ result.entities.length }} 个对象 × {{ result.dimensions.length }} 维度
            </span>
          </div>
          <div ref="chartEl" class="chart-box"></div>
          <div v-if="!result && !loading" class="board-empty">
            <el-icon :size="48" color="#cbd5e1"><Aim /></el-icon>
            <div style="margin-top:12px;color:#94a3b8;">填写维度和打分，点「直接绘图」</div>
          </div>
        </div>

        <div class="qc-panel" v-if="result">
          <div class="qc-panel-hd">📋 打分明细</div>
          <el-table :data="tableData" size="small"
                    :header-cell-style="{background:'#f8fafc',color:'#334155',fontSize:'12px'}">
            <el-table-column prop="dim" label="维度" fixed width="120" />
            <el-table-column v-for="(e, idx) in result.entities" :key="idx"
              :label="e.name" align="right">
              <template #default="{row}">
                <span :class="{'weak-cell': row.weak[idx]}">
                  {{ row.scores[idx].toFixed(1) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div class="weak-summary" v-if="anyWeak">
            <span class="wt-label">⚠️ 短板</span>
            <template v-for="e in result.entities" :key="e.name">
              <span v-if="e.weak_dims.length" class="wt-item">
                {{ e.name }}: {{ e.weak_dims.join('、') }}
              </span>
            </template>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { analyzeRadar, downloadPptx } from '../api'

const topic = ref('')
const maxScore = ref(10)
const weakThreshold = ref(60)  // %
const dimensions = ref([])
const entities = ref([
  { name: '对象 1', scores: [] },
])
const newDim = ref('')
const useLlm = ref(false)
const context = ref('')
const loading = ref(false)
const result = ref(null)
const chartEl = ref(null)
const pptxLoading = ref(false)
let chart = null

const progress = ref(0); const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

const COLORS = ['#0284c7', '#dc2626', '#059669', '#f59e0b', '#7c3aed', '#db2777']

function loadSample() {
  topic.value = 'Q3 供应商综合评估'
  maxScore.value = 10
  weakThreshold.value = 60
  dimensions.value = ['交付', '质量', '成本', '服务', '技术', '沟通']
  entities.value = [
    { name: '供应商 A', scores: [8, 9, 6, 7, 8, 7] },
    { name: '供应商 B', scores: [6, 7, 9, 5, 6, 8] },
    { name: '供应商 C', scores: [7, 8, 7, 8, 9, 6] },
  ]
}

function avg(e) {
  const arr = e.scores.filter(s => s != null)
  return arr.length ? arr.reduce((a,b)=>a+b,0) / arr.length : 0
}
function addDim() {
  const v = newDim.value.trim()
  if (!v || dimensions.value.includes(v)) return
  if (dimensions.value.length >= 12) return ElMessage.warning('最多 12 个维度')
  dimensions.value.push(v)
  entities.value.forEach(e => e.scores.push(Math.round(maxScore.value / 2)))
  newDim.value = ''
}
function removeDim(i) {
  if (dimensions.value.length <= 3) return ElMessage.warning('至少 3 个维度')
  dimensions.value.splice(i, 1)
  entities.value.forEach(e => e.scores.splice(i, 1))
}
function addEntity() {
  entities.value.push({
    name: `对象 ${entities.value.length + 1}`,
    scores: dimensions.value.map(() => Math.round(maxScore.value / 2)),
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
  if (!topic.value.trim()) return ElMessage.warning('请填写主题')
  if (dimensions.value.length < 3) return ElMessage.warning('至少 3 个维度')
  const valid = entities.value.filter(e => e.name?.trim() &&
    e.scores.length === dimensions.value.length &&
    e.scores.every(s => s != null))
  if (!valid.length) return ElMessage.warning('至少 1 个完整对象')

  loading.value = true
  if (useLlm.value) startProgress()
  try {
    const resp = await analyzeRadar({
      topic: topic.value, dimensions: dimensions.value,
      entities: valid.map(e => ({
        name: e.name.trim(), scores: e.scores.map(s => Number(s) || 0)
      })),
      max_score: maxScore.value,
      weak_threshold: weakThreshold.value / 100,
      use_llm: useLlm.value,
      context: useLlm.value ? context.value : '',
    })
    result.value = resp
    await nextTick()
    renderChart()
    if (useLlm.value) stopProgress()
    ElMessage.success(`分析完成，综合最强：${resp.best_entity}`)
  } catch (e) {
    stopProgress()
    ElMessage.error(e.response?.data?.detail || e.message || '失败')
  } finally {
    setTimeout(() => { loading.value = false }, 300)
  }
}

function renderChart() {
  if (!chartEl.value || !result.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  const r = result.value
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: {
      data: r.entities.map(e => e.name),
      orient: 'vertical',
      right: 10, top: 20,
      textStyle: { fontSize: 12, color: '#334155' },
      itemGap: 8,
    },
    radar: {
      center: ['45%', '52%'],
      radius: '65%',
      indicator: r.dimensions.map(d => ({ name: d, max: r.max_score })),
      shape: 'polygon',
      splitNumber: 5,
      axisName: { color: '#334155', fontSize: 12, fontWeight: 500 },
      // 每一圈显示刻度值 (0, 2, 4, 6, 8, 10)
      axisLabel: {
        show: true, showMinLabel: false,
        color: '#94a3b8', fontSize: 10,
        backgroundColor: 'rgba(255,255,255,.85)',
        padding: [1, 3], borderRadius: 2,
      },
      axisTick: { show: true, length: 3, lineStyle: { color: '#cbd5e1' } },
      splitArea: { areaStyle: { color: ['rgba(148,163,184,.04)','rgba(148,163,184,.08)'] } },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    series: [{
      type: 'radar',
      // 数据点上显示得分
      label: {
        show: true,
        formatter: (p) => p.value,
        fontSize: 10, fontWeight: 'bold',
        color: '#0f172a',
        backgroundColor: 'rgba(255,255,255,.9)',
        padding: [2, 4], borderRadius: 3,
        borderWidth: 1, borderColor: 'rgba(148,163,184,.4)',
      },
      symbolSize: 6,
      data: r.entities.map((e, i) => ({
        name: e.name, value: e.scores,
        lineStyle: { color: COLORS[i % COLORS.length], width: 2 },
        areaStyle: { color: COLORS[i % COLORS.length], opacity: 0.15 },
        itemStyle: { color: COLORS[i % COLORS.length] },
      })),
    }],
  })
}

const tableData = computed(() => {
  if (!result.value) return []
  const r = result.value
  return r.dimensions.map((d, i) => ({
    dim: d,
    scores: r.entities.map(e => e.scores[i]),
    weak: r.entities.map(e => e.weak_dims.includes(d)),
  }))
})

const anyWeak = computed(() =>
  result.value?.entities.some(e => e.weak_dims.length) ?? false
)

function exportJson() {
  const blob = new Blob([JSON.stringify(result.value, null, 2)], {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `雷达图_${topic.value}.json`; a.click()
}

async function exportPptx() {
  if (!result.value) return
  pptxLoading.value = true
  try {
    await downloadPptx('radar', result.value, `雷达图_${topic.value}.pptx`)
    ElMessage.success('PPTX 已下载')
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  } finally { pptxLoading.value = false }
}

watch(() => result.value, () => nextTick(renderChart))
window.addEventListener('resize', () => chart?.resize())
onBeforeUnmount(() => {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
  chart?.dispose()
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
  background: #fff; border-radius: 10px; padding: 14px 16px;
  margin-bottom: 12px; border: 1px solid #eef2f7;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.qc-panel-hd {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 600; color: #334155;
  margin-bottom: 10px;
}
.qc-form :deep(.el-form-item) { margin-bottom: 12px; }
.qc-form :deep(.el-form-item__label) { padding-bottom: 4px; font-size: 12px; color: #475569; }
.qc-actions { display: flex; gap: 8px; }
.topic-chip {
  background: #eff6ff; color: #1e40af; padding: 3px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 500;
}

.chips-edit { display: flex; flex-wrap: wrap; padding: 4px;
  background: #f8fafc; border-radius: 6px; min-height: 42px; align-items: center; }

.ent-editor { display: flex; flex-direction: column; gap: 8px; }
.ent-block { background: #f8fafc; border-radius: 8px; padding: 8px 10px; }
.ent-hd { display: flex; align-items: center; margin-bottom: 8px; }
.score-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 6px; }
.score-cell { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.score-lbl { font-size: 11px; color: #64748b; }

.chart-box { width: 100%; height: 400px; }
.board-empty {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  text-align: center; pointer-events: none;
}

.best-chip {
  display: inline-block; background: #ecfdf5; color: #065f46;
  padding: 6px 16px; border-radius: 8px; font-size: 18px; font-weight: 600;
  border: 1px solid #a7f3d0;
}
.leaders { display: flex; flex-direction: column; gap: 4px; }
.leader-row {
  display: flex; justify-content: space-between; padding: 4px 8px;
  background: #f8fafc; border-radius: 4px; font-size: 12.5px;
}
.leader-dim { color: #64748b; }
.leader-who { color: #0f172a; font-weight: 500; }

.weak-cell { color: #dc2626; font-weight: 600; }
.weak-summary {
  margin-top: 10px; padding: 8px 12px; background: #fef2f2;
  border-radius: 6px; font-size: 12.5px; color: #991b1b;
  display: flex; flex-wrap: wrap; gap: 12px; align-items: baseline;
}
.wt-label { font-weight: 600; }

.summary-text {
  color: #334155; line-height: 1.75; font-size: 13px;
  background: #f8fafc; padding: 10px 12px; border-radius: 6px;
  border-left: 3px solid #0284c7; margin-top: 6px;
}
.rec-title { margin: 12px 0 6px; font-weight: 600; color: #0f172a; font-size: 13px; }
.rec-list { padding-left: 20px; color: #334155; line-height: 1.9; margin: 0; font-size: 13px; }
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; }

.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

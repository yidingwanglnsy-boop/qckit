<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#dc2626"><TrendCharts /></el-icon>
        <div>
          <div class="tb-title">柏拉图（Pareto Chart）</div>
          <div class="tb-sub">按频次/成本降序，找出贡献超过阈值的关键少数（Vital Few）</div>
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
      <el-col :md="9" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">📝 输入</div>
          <ToolkitBar :toolkit="toolkit" />
          <el-form label-position="top" size="default" class="qc-form">
            <el-form-item label="主题">
              <el-input v-model="topic" placeholder="如：注塑车间不良类型分布" />
            </el-form-item>
            <el-row :gutter="8">
              <el-col :span="14">
                <el-form-item label="度量单位">
                  <el-select v-model="metric" style="width:100%;">
                    <el-option label="频次（次数）" value="频次" />
                    <el-option label="损失金额（元）" value="损失金额" />
                    <el-option label="工时（小时）" value="工时" />
                    <el-option label="不良数（件）" value="不良数" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="10">
                <el-form-item>
                  <template #label>
                    <span>关键阈值</span>
                    <el-tooltip content="累计占比达到此值的项目视为关键少数（Vital Few）">
                      <el-icon style="margin-left:4px;color:#9ca3af;"><InfoFilled /></el-icon>
                    </el-tooltip>
                  </template>
                  <el-input-number v-model="threshold" :min="10" :max="95" :step="5"
                    style="width:100%;">
                    <template #suffix>%</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item>
              <template #label>
                <span>数据条目</span>
                <span style="color:#9ca3af;font-size:12px;margin-left:6px;">
                  {{ items.length }} 项，可编辑
                </span>
              </template>
              <div class="items-editor">
                <div v-for="(it, i) in items" :key="i" class="item-row">
                  <el-input v-model="it.name" size="small" placeholder="项目名"
                            style="flex: 1;" />
                  <el-input-number v-model="it.value" size="small" :min="0"
                            :controls="false" style="width:100px;" />
                  <el-button size="small" text @click="items.splice(i,1)">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
                <el-button size="small" type="primary" plain
                  @click="items.push({name:'',value:0})"
                  style="width:100%;margin-top:6px;">
                  <el-icon><Plus /></el-icon>&nbsp;添加项目
                </el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="useLlm">
                <span style="font-size:13px;">调用 LLM 生成洞察和改善建议</span>
                <el-tooltip content="需 1-3 分钟。仅需要画图时可关闭">
                  <el-icon style="margin-left:4px;color:#9ca3af;"><InfoFilled /></el-icon>
                </el-tooltip>
              </el-checkbox>
            </el-form-item>
            <el-form-item v-if="useLlm" label="背景（可选）">
              <el-input v-model="context" type="textarea" :rows="2" resize="none"
                placeholder="行业/场景/关注点" />
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
          <ul class="stage-list">
            <li v-for="(s,i) in stages" :key="i"
                :class="i < stageIdx ? 'done' : i === stageIdx ? 'active' : ''">
              <span class="dot">{{ i < stageIdx ? '✓' : i === stageIdx ? '●' : '○' }}</span>
              <span>{{ s }}</span>
            </li>
          </ul>
        </div>
        </transition>

        <transition name="fade">
        <div class="qc-panel" v-if="result">
          <div class="qc-panel-hd">
            🎯 关键少数（累计 ≥ {{ result.threshold }}%）
          </div>
          <div class="vital-list">
            <div v-for="n in result.vital_few" :key="n" class="vital-chip">{{ n }}</div>
          </div>
          <template v-if="result.insights">
            <div class="rec-title">💡 洞察</div>
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

      <el-col :md="15" :xs="24">
        <div class="qc-panel" style="min-height: 400px; position: relative;">
          <div class="qc-panel-hd">
            <span>📊 柏拉图</span>
            <span v-if="result" class="topic-chip">
              合计 {{ result.total }} {{ result.metric }} · 关键少数 {{ result.vital_few.length }} 项 · 阈值 {{ result.threshold }}%
            </span>
          </div>
          <div ref="chartEl" class="chart-box"></div>
          <div v-if="!result && !loading" class="board-empty">
            <el-icon :size="48" color="#cbd5e1"><TrendCharts /></el-icon>
            <div style="margin-top:12px;color:#94a3b8;">填写左侧数据，点「直接绘图」</div>
          </div>
        </div>

        <div class="qc-panel" v-if="result">
          <div class="qc-panel-hd">📋 数据明细</div>
          <el-table :data="result.items" size="small" :cell-style="cellStyle"
                    :header-cell-style="{background:'#f8fafc',color:'#334155',fontSize:'12px'}">
            <el-table-column type="index" label="#" width="45" />
            <el-table-column prop="name" label="项目" />
            <el-table-column prop="value" :label="result.metric" width="90" align="right" />
            <el-table-column label="占比" width="80" align="right">
              <template #default="{row}">{{ row.percent.toFixed(1) }}%</template>
            </el-table-column>
            <el-table-column label="累计占比" width="90" align="right">
              <template #default="{row}">
                <span :class="{'vital-cum': row.is_vital_few}">
                  {{ row.cumulative_percent.toFixed(1) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="标记" width="80" align="center">
              <template #default="{row}">
                <el-tag v-if="row.is_vital_few" type="danger" size="small">关键</el-tag>
                <el-tag v-else type="info" size="small" effect="plain">次要</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <NextStepBar :from="'pareto'" :topic="topic || ''" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onBeforeUnmount, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { analyzePareto, downloadPptx } from '../api'
import ToolkitBar from '../components/ToolkitBar.vue'
import NextStepBar from '../components/NextStepBar.vue'
import { useToolkit } from '../composables/useToolkit'

const topic = ref('注塑车间不良类型分布')
const metric = ref('频次')
const threshold = ref(80)
const useLlm = ref(false)
const context = ref('')
const items = ref([])
const loading = ref(false)
const result = ref(null)
const chartEl = ref(null)
let chart = null

// —— 示例数据 & 历史记录 —— //
const form = reactive({ topic: topic.value, metric: metric.value, threshold: threshold.value, raw_data: '' })
watch(form, () => {
  if (form.topic !== undefined) topic.value = form.topic
  if (form.metric !== undefined) metric.value = form.metric
  if (form.threshold !== undefined) threshold.value = form.threshold
  if (form.raw_data !== undefined && form.raw_data) {
    // "name,value" per line -> items[]
    const parsed = String(form.raw_data).split(/\r?\n/).map(l => l.trim()).filter(Boolean)
      .map(line => {
        const [name, val] = line.split(',')
        return { name: (name || '').trim(), value: Number(val) || 0 }
      }).filter(it => it.name)
    if (parsed.length) items.value = parsed
  }
}, { deep: true })
const toolkit = useToolkit('pareto', form)

const stages = ['发送请求到 LLM', '模型分析（1-3 分钟）', '整理结果', '渲染图表']
const stageIdx = ref(0); const progress = ref(0); const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null
const pptxLoading = ref(false)

// 关键少数用同一红色系;虚线也是同色 —— 视觉上一眼对应
const VITAL_COLOR = '#dc2626'
const NORMAL_COLOR = '#94a3b8'
const CUM_COLOR = '#f59e0b'

function loadSample() {
  topic.value = '注塑车间不良类型分布'
  metric.value = '频次'
  threshold.value = 80
  context.value = '3 号注塑机近 30 天不良记录'
  items.value = [
    { name: '尺寸超差', value: 128 },
    { name: '表面缺陷', value: 96 },
    { name: '缩痕', value: 54 },
    { name: '批锋/毛边', value: 31 },
    { name: '颜色偏差', value: 18 },
    { name: '其他', value: 12 },
    { name: '包装损伤', value: 7 },
  ]
}

function startProgress() {
  progress.value = 0; elapsed.value = 0; stageIdx.value = 0
  setTimeout(() => { stageIdx.value = 1; progress.value = 10 }, 300)
  progressTimer = setInterval(() => {
    if (progress.value < 88)
      progress.value = Math.min(88, progress.value + Math.max(0.3, (88 - progress.value) * 0.015))
  }, 600)
  elapsedTimer = setInterval(() => { elapsed.value += 1 }, 1000)
}
function stopProgress(ok) {
  clearInterval(progressTimer); clearInterval(elapsedTimer)
  progressTimer = elapsedTimer = null
  if (ok) { stageIdx.value = 3; progress.value = 100 }
}

async function run() {
  const clean = items.value.filter(i => i.name?.trim() && i.value > 0)
  if (clean.length < 2) return ElMessage.warning('至少 2 个有效数据项')
  if (!topic.value.trim()) return ElMessage.warning('请填写主题')

  loading.value = true
  if (useLlm.value) startProgress()
  try {
    const resp = await analyzePareto({
      topic: topic.value, metric: metric.value,
      threshold: threshold.value, use_llm: useLlm.value,
      context: useLlm.value ? context.value : '',
      items: clean.map(i => ({ name: i.name.trim(), value: Number(i.value) })),
    })
    if (useLlm.value) { stageIdx.value = 2; progress.value = 92 }
    result.value = resp
    toolkit.saveHistory(resp, {
      topic: topic.value, metric: metric.value, threshold: threshold.value,
      raw_data: clean.map(i => `${i.name},${i.value}`).join('\n'),
    })
    await nextTick()
    renderChart()
    if (useLlm.value) stopProgress(true)
    const msg = useLlm.value
      ? `分析完成，关键少数 ${resp.vital_few.length} 项 / 用时 ${elapsed.value}s`
      : `绘图完成，关键少数 ${resp.vital_few.length} 项`
    ElMessage.success(msg)
  } catch (e) {
    stopProgress(false)
    ElMessage.error(e.response?.data?.detail || e.message || '失败')
  } finally {
    setTimeout(() => { loading.value = false }, 300)
  }
}

function renderChart() {
  if (!chartEl.value || !result.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  const r = result.value
  const cats = r.items.map(i => i.name)
  // 柱：关键少数=红，其它=灰。累计折线上关键点=红，其余=黄
  const bars = r.items.map(i => ({
    value: i.value,
    itemStyle: {
      color: i.is_vital_few ? VITAL_COLOR : NORMAL_COLOR,
      borderRadius: [4, 4, 0, 0],
    },
  }))
  const cumPts = r.items.map(i => ({
    value: i.cumulative_percent,
    itemStyle: { color: i.is_vital_few ? VITAL_COLOR : CUM_COLOR },
    // 关键少数节点用大一号 + 红色圆圈突出
    symbolSize: i.is_vital_few ? 12 : 8,
  }))
  chart.setOption({
    grid: { left: 60, right: 60, top: 40, bottom: 80 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: [r.metric, '累计占比'], top: 8, textStyle: { fontSize: 11 } },
    xAxis: {
      type: 'category', data: cats,
      axisLabel: { rotate: cats.length > 5 ? 25 : 0, fontSize: 11, color: '#475569' },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    yAxis: [
      { type: 'value', name: r.metric, axisLabel: { fontSize: 11, color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9' } } },
      { type: 'value', name: '累计 %', position: 'right', max: 100,
        axisLabel: { formatter: '{value}%', fontSize: 11, color: '#64748b' },
        splitLine: { show: false } },
    ],
    series: [
      { name: r.metric, type: 'bar', data: bars, barMaxWidth: 40, yAxisIndex: 0 },
      {
        name: '累计占比', type: 'line', yAxisIndex: 1, data: cumPts,
        lineStyle: { color: CUM_COLOR, width: 2.5 },
        symbol: 'circle',
        label: {
          show: true, position: 'top',
          formatter: (p) => `${p.value.toFixed(0)}%`,
          fontSize: 10, fontWeight: 'bold',
          color: (p) => r.items[p.dataIndex].is_vital_few ? VITAL_COLOR : '#b45309',
        },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: VITAL_COLOR, type: 'dashed', width: 1.4 },
          label: {
            formatter: `${r.threshold}%`, color: VITAL_COLOR,
            fontSize: 11, fontWeight: 'bold', position: 'insideEndTop',
          },
          data: [{ yAxis: r.threshold }],
        },
      },
    ],
  })
}

function cellStyle({ row }) {
  return row.is_vital_few ? { background: '#fef2f2' } : {}
}

function exportJson() {
  const blob = new Blob([JSON.stringify(result.value, null, 2)], {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `柏拉图_${topic.value}.json`; a.click()
}

async function exportPptx() {
  if (!result.value) return
  pptxLoading.value = true
  try {
    await downloadPptx('pareto', result.value, `柏拉图_${topic.value}.pptx`)
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
  background: #fef2f2; color: #991b1b; padding: 3px 10px;
  border-radius: 6px; font-size: 12px; font-weight: 500;
}

.items-editor { display: flex; flex-direction: column; gap: 6px; }
.item-row {
  display: flex; gap: 6px; align-items: center;
  background: #f8fafc; padding: 4px; border-radius: 6px;
}

.chart-box { width: 100%; height: 380px; }
.board-empty {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  text-align: center; pointer-events: none;
}

.stage-list { list-style: none; padding: 0; margin: 12px 0 0; font-size: 12.5px; }
.stage-list li { display: flex; align-items: center; gap: 8px; padding: 4px 0; color: #94a3b8; }
.stage-list li.done { color: #10b981; }
.stage-list li.active { color: #dc2626; font-weight: 500; }
.stage-list .dot { width: 14px; text-align: center; }

.vital-list { display: flex; flex-wrap: wrap; gap: 6px; }
.vital-chip {
  background: #fef2f2; color: #991b1b; padding: 4px 10px;
  border-radius: 6px; font-size: 12.5px; border: 1px solid #fecaca;
  font-weight: 500;
}
.vital-cum { color: #dc2626; font-weight: 600; }

.summary-text {
  color: #334155; line-height: 1.75; font-size: 13px;
  background: #f8fafc; padding: 10px 12px; border-radius: 6px;
  border-left: 3px solid #dc2626; margin-top: 6px;
}
.rec-title { margin: 14px 0 4px; font-weight: 600; color: #0f172a; font-size: 13px; }
.rec-list { padding-left: 20px; color: #334155; line-height: 1.9; margin: 0; font-size: 13px; }
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; }

.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

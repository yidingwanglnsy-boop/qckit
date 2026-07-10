<template>
  <div>
    <div class="qc-hero">
      <h1>关联图 · Relations Diagram</h1>
      <p>输入问题主题与候选原因节点，LLM 自动识别核心/关键/传导节点并推断因果关系。</p>
    </div>

    <el-row :gutter="16">
      <el-col :md="9">
        <div class="qc-card">
          <el-form label-position="top">
            <el-form-item label="问题主题">
              <el-input v-model="topic" placeholder="如：产线A车间不良率高" />
            </el-form-item>
            <el-form-item label="候选节点（每行一个）">
              <el-input
                v-model="nodesText" type="textarea" :rows="10"
                placeholder="来料检验松&#10;工人培训不足&#10;设备老化&#10;标准作业书缺失&#10;车间温湿度波动&#10;班组长巡检少" />
            </el-form-item>
            <el-form-item label="补充背景（可选）">
              <el-input v-model="context" type="textarea" :rows="2"
                placeholder="行业/工艺/近期变更等背景信息" />
            </el-form-item>
            <el-button type="primary" :loading="loading" @click="run" style="width:100%;">
              <el-icon><MagicStick /></el-icon>&nbsp;开始分析
            </el-button>
            <el-button @click="loadSample" style="width:100%;margin:8px 0 0 0;">载入示例</el-button>
          </el-form>
        </div>

        <div class="qc-card" v-if="result">
          <b>图例</b>
          <div class="qc-legend" style="margin-top:8px;">
            <span class="qc-tag-core">● 核心节点</span>
            <span class="qc-tag-key">● 关键节点</span>
            <span class="qc-tag-conduct">● 传导节点</span>
            <span class="qc-tag-normal">● 一般节点</span>
          </div>
          <el-divider />
          <b>整体解读</b>
          <p style="color:#374151;line-height:1.7;">{{ result.summary }}</p>
          <b>改善建议</b>
          <ol style="color:#374151;line-height:1.8;padding-left:20px;">
            <li v-for="(r,i) in result.recommendations" :key="i">{{ r }}</li>
          </ol>
        </div>
      </el-col>

      <el-col :md="15">
        <div class="qc-card" style="position:relative;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <b>关联图可视化</b>
            <div>
              <el-button size="small" @click="relayout" :disabled="!result">重新布局</el-button>
              <el-button size="small" type="primary" @click="exportPng" :disabled="!result">导出 PNG</el-button>
              <el-button size="small" @click="exportJson" :disabled="!result">导出 JSON</el-button>
            </div>
          </div>
          <div ref="cyEl" style="height:560px;background:#fafafa;border-radius:8px;border:1px solid #e5e7eb;"></div>
          <el-empty v-if="!result && !loading" description="填写左侧信息后开始分析" style="position:absolute;top:60px;left:0;right:0;pointer-events:none;" />
        </div>

        <div class="qc-card" v-if="result">
          <b>节点详情</b>
          <el-table :data="result.nodes" size="small" style="margin-top:6px;">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="label" label="节点" />
            <el-table-column label="角色" width="110">
              <template #default="{row}">
                <span :class="'qc-tag-'+row.role" style="padding:2px 10px;border-radius:999px;font-size:12px;">
                  {{ roleName(row.role) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="出/入度" width="80">
              <template #default="{row}">{{ row.out_degree }} / {{ row.in_degree }}</template>
            </el-table-column>
            <el-table-column prop="reason" label="判定依据" show-overflow-tooltip />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import cytoscape from 'cytoscape'
import fcose from 'cytoscape-fcose'
import { analyzeRelations } from '../api'

cytoscape.use(fcose)

const topic = ref('产线A车间不良率高')
const nodesText = ref('')
const context = ref('')
const loading = ref(false)
const result = ref(null)
const cyEl = ref(null)
let cy = null

const ROLE_COLOR = {
  core:    '#ef4444',
  key:     '#f59e0b',
  conduct: '#3b82f6',
  normal:  '#9ca3af',
}
const ROLE_SIZE = { core: 68, key: 56, conduct: 46, normal: 38 }
const ROLE_NAME = { core:'核心', key:'关键', conduct:'传导', normal:'一般' }
const roleName = (r) => ROLE_NAME[r] || r

function loadSample(){
  topic.value = '产线A车间不良率高'
  nodesText.value = ['来料检验松','工人培训不足','设备老化','标准作业书缺失',
    '车间温湿度波动','班组长巡检少','换型频繁','首件确认流于形式'].join('\n')
  context.value = '注塑车间，近3月不良率从0.8%升到2.1%'
}

async function run(){
  const nodes = nodesText.value.split('\n').map(s=>s.trim()).filter(Boolean)
  if (nodes.length < 2) { ElMessage.warning('至少输入 2 个节点'); return }
  if (!topic.value.trim()) { ElMessage.warning('请填写问题主题'); return }
  loading.value = true
  try {
    result.value = await analyzeRelations({ topic: topic.value, nodes, context: context.value })
    await nextTick()
    render()
  } catch(e){
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally { loading.value = false }
}

function render(){
  const r = result.value
  const elements = [
    ...r.nodes.map(n => ({
      data: { id: n.id, label: n.label, role: n.role,
              color: ROLE_COLOR[n.role], size: ROLE_SIZE[n.role] }
    })),
    ...r.edges.map((e, i) => ({
      data: { id: 'e'+i, source: e.source, target: e.target,
              label: e.label, width: 1 + e.strength }
    }))
  ]
  if (cy) cy.destroy()
  cy = cytoscape({
    container: cyEl.value,
    elements,
    style: [
      { selector: 'node', style: {
          'background-color': 'data(color)',
          'label': 'data(label)',
          'width': 'data(size)', 'height': 'data(size)',
          'color': '#111827', 'font-size': 13,
          'text-valign': 'bottom', 'text-margin-y': 6,
          'text-wrap': 'wrap', 'text-max-width': 120,
          'border-width': 2, 'border-color': '#fff',
          'box-shadow': '0 2px 8px rgba(0,0,0,.15)'
      }},
      { selector: 'edge', style: {
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'width': 'data(width)',
          'line-color': '#94a3b8', 'target-arrow-color': '#94a3b8',
          'label': 'data(label)', 'font-size': 10, 'color': '#475569',
          'text-background-color': '#fff', 'text-background-opacity': 0.85,
          'text-background-padding': 2
      }},
      { selector: 'node[role="core"]', style: {
          'border-width': 4, 'border-color': '#fca5a5', 'font-weight': 'bold'
      }}
    ],
    layout: { name: 'fcose', animate: true, nodeSeparation: 90, idealEdgeLength: 130 }
  })
}

function relayout(){ if (cy) cy.layout({ name:'fcose', animate:true }).run() }

function exportPng(){
  if (!cy) return
  const png = cy.png({ full:true, scale:2, bg:'#ffffff' })
  const a = document.createElement('a')
  a.href = png; a.download = `关联图_${topic.value}.png`; a.click()
}
function exportJson(){
  const blob = new Blob([JSON.stringify(result.value, null, 2)], {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `关联图_${topic.value}.json`; a.click()
}
</script>

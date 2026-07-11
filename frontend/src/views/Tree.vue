<template>
  <ToolPage
    tool-key="tree" title="系统图（Tree Diagram）" icon-name="Grid"
    subtitle="把大目标层层拆到可执行行动 · 叶节点 SMART 化 + 优先级"
    :form="form" :analyze-fn="doAnalyze"
    :build-payload="(f, r) => ({ topic: f.topic, ...r })"
    :pptx-filename="f => `系统图_${f.topic || 'tree'}.pptx`">
    <template #inputs>
      <el-form label-position="top" size="default">
        <el-form-item label="顶层目标（一句话）">
          <el-input v-model="form.topic" placeholder="如：3 个月内将不良率降至 1.2%" />
        </el-form-item>
        <el-form-item label="背景（可选）">
          <el-input v-model="form.context" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="目标层数">
          <el-radio-group v-model="form.layers">
            <el-radio-button :value="2">2 层</el-radio-button>
            <el-radio-button :value="3">3 层</el-radio-button>
            <el-radio-button :value="4">4 层</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="已有想法（可选，逗号分隔）">
          <el-input v-model="hintsRaw" placeholder="培训、SOP、巡检" />
        </el-form-item>
      </el-form>
    </template>

    <template #results="{ result }">
      <div v-if="result.summary" class="result-section">
        <h4>💡 整体解读</h4>
        <div>{{ result.summary }}</div>
      </div>
      <div class="result-section">
        <h4>🌳 层级树（{{ (result.nodes || []).length }} 节点）</h4>
        <div v-for="lvl in maxLevel(result) + 1" :key="lvl-1"
             style="margin: 4px 0; padding-left: 4px;">
          <b style="color:#6366f1;">L{{ lvl-1 }}:</b>
          <span v-for="n in nodesAt(result, lvl-1)" :key="n.id"
                :style="chipStyle(n)">
            {{ n.label }}
            <el-tag v-if="n.priority" size="small" :type="prioType(n.priority)"
                    style="margin-left:4px;">{{ n.priority }}</el-tag>
          </span>
        </div>
      </div>
      <div v-if="result.mece_check?.length" class="result-section">
        <h4>🔍 MECE 反思</h4>
        <ul style="margin:0;padding-left:18px;">
          <li v-for="(m,i) in result.mece_check" :key="i">{{ m }}</li>
        </ul>
      </div>
      <div v-if="result.recommendations?.length" class="result-section">
        <h4>🎯 优先行动建议</h4>
        <ol style="margin:0;padding-left:18px;">
          <li v-for="(r,i) in result.recommendations" :key="i">{{ r }}</li>
        </ol>
      </div>
    </template>
  </ToolPage>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import ToolPage from '../components/ToolPage.vue'
import { analyzeTree } from '../api'

const form = reactive({ topic: '', context: '', layers: 3, hints: [] })
const hintsRaw = ref('')
watch(hintsRaw, v => {
  form.hints = v ? v.split(/[,，、\s]+/).filter(Boolean) : []
})
watch(() => form.hints, v => {
  const s = (v || []).join(', ')
  if (s !== hintsRaw.value) hintsRaw.value = s
})

async function doAnalyze (f) {
  return await analyzeTree({
    topic: f.topic, context: f.context || null,
    layers: f.layers, hints: f.hints,
  })
}

function maxLevel (r) {
  return Math.max(0, ...(r.nodes || []).map(n => n.level || 0))
}
function nodesAt (r, lvl) {
  return (r.nodes || []).filter(n => (n.level || 0) === lvl)
}
function chipStyle (n) {
  const bg = n.level === 0 ? '#1e40af'
    : n.is_leaf ? (n.priority === 'P1' ? '#fee2e2' : n.priority === 'P2' ? '#fef3c7' : '#f0fdf4')
    : '#e0e7ff'
  const fg = n.level === 0 ? '#fff' : '#1e293b'
  return `display:inline-block;margin:2px 4px;padding:2px 8px;border-radius:4px;background:${bg};color:${fg};font-size:12px;`
}
function prioType (p) {
  return p === 'P1' ? 'danger' : p === 'P2' ? 'warning' : 'success'
}
</script>

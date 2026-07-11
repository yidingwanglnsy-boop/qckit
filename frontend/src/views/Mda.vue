<template>
  <ToolPage
    tool-key="mda" title="矩阵数据解析（Matrix Data Analysis）" icon-name="DataAnalysis"
    subtitle="多对象 × 多指标数据 2D PCA 降维 · AI 解读象限定位"
    :form="form" :analyze-fn="doAnalyze"
    :build-payload="(f, r) => r"
    :pptx-filename="f => `矩阵数据解析_${f.topic || 'mda'}.pptx`">
    <template #inputs>
      <el-form label-position="top" size="default">
        <el-form-item label="分析主题">
          <el-input v-model="form.topic" placeholder="如：5 家供应商综合评估" />
        </el-form-item>
        <el-form-item label="指标（逗号分隔）">
          <el-input v-model="form.metrics_text" placeholder="质量, 交期, 价格, 服务, 技术" />
        </el-form-item>
        <el-form-item label="越低越好的指标（逗号分隔，可选）">
          <el-input v-model="form.lower_is_better_text"
                    placeholder="交期, 价格" />
          <div style="font-size:11px;color:#94a3b8;margin-top:2px;">
            💡 会自动反向归一，让"高分=好"始终成立
          </div>
        </el-form-item>
        <el-form-item label="对象数据（CSV 格式：对象名, v1, v2, ...）">
          <el-input v-model="form.subjects_text" type="textarea" :rows="6"
                    placeholder="供应商A, 9, 7, 8, 9, 8&#10;供应商B, 8, 9, 7, 7, 9" />
        </el-form-item>
      </el-form>
    </template>

    <template #results="{ result }">
      <div class="result-section">
        <h4>📐 主成分</h4>
        <b>PC1 = {{ result.pc1_name }}</b>
        <span style="color:#94a3b8;">
          ({{ ((result.variance_ratio || [0])[0] * 100).toFixed(0) }}%)
        </span>
        &nbsp;·&nbsp;
        <b>PC2 = {{ result.pc2_name }}</b>
        <span style="color:#94a3b8;">
          ({{ ((result.variance_ratio || [0,0])[1] * 100).toFixed(0) }}%)
        </span>
      </div>
      <div class="result-section">
        <h4>📍 象限分布</h4>
        <div class="quad-grid">
          <div v-for="q in ['2','1','3','4']" :key="q" class="quad" :class="'q-'+q">
            <div class="quad-hd">
              <b>第 {{ ['','I','II','III','IV'][+q] }} 象限</b>
              &nbsp;<span>{{ result.quadrant_labels?.[q] }}</span>
            </div>
            <div class="quad-body">
              <el-tag v-for="p in ptsInQuad(result, +q)" :key="p.name" size="small"
                      style="margin:2px;">{{ p.name }}</el-tag>
              <div v-if="result.quadrant_insights?.[q]"
                   style="margin-top:6px;color:#475569;font-size:12px;">
                💡 {{ result.quadrant_insights[q] }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="result.recommendations?.length" class="result-section">
        <h4>🎯 决策建议</h4>
        <ol style="margin:0;padding-left:18px;">
          <li v-for="(r,i) in result.recommendations" :key="i">{{ r }}</li>
        </ol>
      </div>
    </template>
  </ToolPage>
</template>

<script setup>
import { reactive } from 'vue'
import ToolPage from '../components/ToolPage.vue'
import { analyzeMda } from '../api'
import { ElMessage } from 'element-plus'

const form = reactive({
  topic: '', metrics_text: '', lower_is_better_text: '', subjects_text: '',
})

async function doAnalyze (f) {
  const metrics = f.metrics_text.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  const lower = f.lower_is_better_text.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  const subjects = f.subjects_text.split('\n').map(line => {
    const parts = line.split(/[,，]/).map(s => s.trim())
    if (parts.length < 2) return null
    return { name: parts[0], values: parts.slice(1).map(Number) }
  }).filter(Boolean)
  if (metrics.length < 2 || subjects.length < 2) {
    ElMessage.warning('请填写至少 2 个指标和 2 个对象')
    throw new Error('invalid')
  }
  return await analyzeMda({
    topic: f.topic, metric_names: metrics,
    subjects, lower_is_better: lower,
  })
}

function ptsInQuad (r, q) {
  return (r.points || []).filter(p => p.quadrant === q)
}
</script>

<style scoped>
.quad-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.quad { border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; }
.q-1 { background: #d1fae5; }
.q-2 { background: #fef3c7; }
.q-3 { background: #fee2e2; }
.q-4 { background: #dbeafe; }
.quad-hd { font-size: 13px; margin-bottom: 4px; color: #1e293b; }
</style>

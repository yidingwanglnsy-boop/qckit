<template>
  <ToolPage
    tool-key="pdpc" title="PDPC 过程决策程序图" icon-name="Compass"
    subtitle="前瞻性列出流程各步的风险 × 对策 · 预防性思维"
    :form="form" :analyze-fn="doAnalyze"
    :build-payload="(f, r) => r"
    :pptx-filename="f => `PDPC_${f.topic || 'pdpc'}.pptx`">
    <template #inputs>
      <el-form label-position="top" size="default">
        <el-form-item label="目标事件">
          <el-input v-model="form.topic" placeholder="如：12 月新产品量产上线" />
        </el-form-item>
        <el-form-item label="主流程步骤（每行一条，可选，AI 会补充）">
          <el-input v-model="form.steps_text" type="textarea" :rows="3"
                    placeholder="物料到位&#10;试产验证&#10;量产切换" />
        </el-form-item>
        <el-form-item label="关注风险维度（逗号分隔，可选）">
          <el-input v-model="form.risk_dims_text"
                    placeholder="供应, 技术, 质量, 进度" />
        </el-form-item>
        <el-form-item label="背景（可选）">
          <el-input v-model="form.context" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </template>

    <template #results="{ result }">
      <div v-if="result.summary" class="result-section">
        <h4>💡 整体解读</h4>{{ result.summary }}
      </div>
      <div class="result-section">
        <h4>🗺 展开图（{{ steps(result).length }} 步 · {{ risks(result).length }} 风险 · {{ cms(result).length }} 对策）</h4>
        <div v-for="s in steps(result)" :key="s.id" class="step-block">
          <div class="step-hd">📌 {{ s.label }}</div>
          <div v-for="r in risksOf(result, s.id)" :key="r.id"
               class="risk-block" :class="'p-'+r.priority">
            <div>
              ⚠️ <b>{{ r.label }}</b>
              <el-tag size="small" :type="prioType(r.priority)"
                      style="margin-left:6px;">
                {{ r.priority }} · P={{ r.probability }} I={{ r.impact }}
              </el-tag>
            </div>
            <div v-for="cm in cmsOf(result, r.id)" :key="cm.id" class="cm-block">
              ✅ {{ cm.label }}
              <span v-if="cm.trigger" style="color:#64748b;font-size:11px;">
                （触发: {{ cm.trigger }}）
              </span>
              <span v-if="cm.owner" style="color:#6366f1;font-size:11px;">
                @{{ cm.owner }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div v-if="result.top_risks?.length" class="result-section">
        <h4>🚨 Top 高危路径</h4>
        <ul style="margin:0;padding-left:18px;">
          <li v-for="(r,i) in result.top_risks" :key="i">
            <b>{{ r.risk }}</b> → {{ r.action }} <span style="color:#94a3b8;">(score {{ r.score }})</span>
          </li>
        </ul>
      </div>
      <div v-if="result.recommendations?.length" class="result-section">
        <h4>🛡 预案要点</h4>
        <ol style="margin:0;padding-left:18px;">
          <li v-for="(r,i) in result.recommendations" :key="i">{{ r }}</li>
        </ol>
      </div>
    </template>
  </ToolPage>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import ToolPage from '../components/ToolPage.vue'
import { analyzePdpc } from '../api'

const form = reactive({
  topic: '', steps_text: '', risk_dims_text: '', context: '',
})

async function doAnalyze (f) {
  if (!f.topic?.trim()) {
    ElMessage.warning('请填写目标事件'); throw new Error('invalid')
  }
  const steps = f.steps_text.split('\n').map(s => s.trim()).filter(Boolean)
  const risk_dims = f.risk_dims_text.split(/[,，]/).map(s => s.trim()).filter(Boolean)
  return await analyzePdpc({
    topic: f.topic,
    steps: steps.length ? steps : null,
    risk_dims: risk_dims.length ? risk_dims : null,
    context: f.context || null,
  })
}

function steps (r) { return (r.nodes || []).filter(n => n.kind === 'step') }
function risks (r) { return (r.nodes || []).filter(n => n.kind === 'risk') }
function cms (r) { return (r.nodes || []).filter(n => n.kind === 'countermeasure') }
function risksOf (r, sid) { return risks(r).filter(x => x.parent === sid) }
function cmsOf (r, rid) { return cms(r).filter(x => x.parent === rid) }
function prioType (p) {
  return p === 'P1' ? 'danger' : p === 'P2' ? 'warning' : 'info'
}
</script>

<style scoped>
.step-block { margin-bottom: 12px; }
.step-hd {
  font-weight: 600; color: #fff; background: #1e40af;
  padding: 6px 10px; border-radius: 4px 4px 0 0;
}
.risk-block {
  padding: 8px 10px; margin-top: 4px; border-radius: 4px;
  border-left: 4px solid transparent;
}
.risk-block.p-P1 { background: #fef2f2; border-left-color: #dc2626; }
.risk-block.p-P2 { background: #fef3c7; border-left-color: #d97706; }
.risk-block.p-P3 { background: #f1f5f9; border-left-color: #64748b; }
.cm-block {
  margin: 4px 0 4px 20px; padding: 4px 8px;
  background: #d1fae5; border-radius: 4px; font-size: 12px;
}
</style>

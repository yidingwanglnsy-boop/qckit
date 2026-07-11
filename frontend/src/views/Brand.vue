<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#7c3aed"><Brush /></el-icon>
        <div>
          <div class="tb-title">品牌主题（Brand Theme）</div>
          <div class="tb-sub">一次配置，Excel / PPTX 等所有导出物统一使用公司色 & 字体</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button @click="reload">
          <el-icon><RefreshLeft /></el-icon>&nbsp;重置为预设
        </el-button>
        <el-button type="primary" :loading="saving" @click="save">
          <el-icon><Check /></el-icon>&nbsp;保存
        </el-button>
      </div>
    </div>

    <el-row :gutter="14">
      <el-col :md="10" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">🎨 预设方案</div>
          <div class="preset-grid">
            <div v-for="(p, k) in presets" :key="k"
                 class="preset-card" @click="applyPreset(k)">
              <div class="swatches">
                <span :style="`background:#${p.primary}`" />
                <span :style="`background:#${p.secondary}`" />
                <span :style="`background:#${p.accent}`" />
                <span :style="`background:#${p.warn}`" />
              </div>
              <div class="preset-name">{{ p.name }}</div>
            </div>
          </div>
        </div>

        <div class="qc-panel">
          <div class="qc-panel-hd">🖌 主题参数</div>
          <el-form label-position="top" size="default">
            <el-form-item label="主题名称">
              <el-input v-model="form.name" />
            </el-form-item>
            <el-form-item label="公司名（Excel 页眉/PPT 副标题，可选）">
              <el-input v-model="form.company" placeholder="如：XX 制造有限公司" />
            </el-form-item>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="中文字体">
                  <el-select v-model="form.font_zh">
                    <el-option v-for="f in fontsZh" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="英文字体">
                  <el-select v-model="form.font_en">
                    <el-option v-for="f in fontsEn" :key="f" :label="f" :value="f" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider>颜色（点色块开画布 · 或输入 HEX / RGB）</el-divider>
            <el-form-item v-for="k in colorKeys" :key="k" :label="colorLabels[k]">
              <div class="color-row">
                <el-color-picker :model-value="'#' + form[k]"
                  @update:model-value="v => form[k] = (v || '').replace('#','').toUpperCase()" />
                <span class="hex-prefix">#</span>
                <input class="hex-input" maxlength="6" :value="form[k]"
                  @input="e => form[k] = e.target.value.replace('#','').toUpperCase()" />
                <span class="rgb-sep">RGB</span>
                <input class="rgb-input" type="number" min="0" max="255"
                  :value="hexToRgb(form[k])[0]"
                  @input="e => form[k] = rgbToHex(+e.target.value, hexToRgb(form[k])[1], hexToRgb(form[k])[2])" />
                <input class="rgb-input" type="number" min="0" max="255"
                  :value="hexToRgb(form[k])[1]"
                  @input="e => form[k] = rgbToHex(hexToRgb(form[k])[0], +e.target.value, hexToRgb(form[k])[2])" />
                <input class="rgb-input" type="number" min="0" max="255"
                  :value="hexToRgb(form[k])[2]"
                  @input="e => form[k] = rgbToHex(hexToRgb(form[k])[0], hexToRgb(form[k])[1], +e.target.value)" />
                <span class="color-hint">{{ colorHints[k] }}</span>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <el-col :md="14" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">👁 实时预览（Excel 表格样式）</div>
          <div class="preview-shell" :style="previewShellStyle">
            <div class="preview-title" :style="previewTitleStyle">
              5W2H 分析 · 焊接工序不良率
            </div>
            <div v-if="form.company" class="preview-company">{{ form.company }}</div>
            <table class="preview-table" :style="previewTableStyle">
              <thead>
                <tr>
                  <th :style="thStyle">#</th>
                  <th :style="th2Style">根因 (Why)</th>
                  <th :style="thStyle">对象 (What)</th>
                  <th :style="thStyle">责任人</th>
                  <th :style="thStyle">是否要因</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td :style="idxStyle">1</td>
                  <td :style="keyStyle">焊工作业标准执行不到位</td>
                  <td :style="plainStyle">焊枪角度偏差</td>
                  <td :style="plainStyle">张三</td>
                  <td :style="accentStyle">是</td>
                </tr>
                <tr>
                  <td :style="idxStyle">2</td>
                  <td :style="keyStyle">保护气流量表偏差</td>
                  <td :style="aiStyle">🤖 气孔率上升</td>
                  <td :style="plainStyle">李四</td>
                  <td :style="mutedStyle">否</td>
                </tr>
                <tr>
                  <td :style="idxStyle">3</td>
                  <td :style="keyStyle">焊丝直径公差偏大</td>
                  <td :style="aiStyle">🤖 送丝抖动</td>
                  <td :style="plainStyle">王五</td>
                  <td :style="aiStyle">🤖 待验证</td>
                </tr>
              </tbody>
            </table>
            <div class="preview-legend">
              <span :style="`background:#${form.primary}`" />主色/表头
              <span :style="`background:#${form.secondary}`" />辅色/分组
              <span :style="`background:#${form.accent}`" />强调/要因
              <span :style="`background:#${form.warn}`" />AI 补全
            </div>
          </div>
          <div class="tip-bar" style="margin-top:12px;">
            💡 预览与真实 Excel 视觉一致（颜色、字体、层次）。保存后立即对所有导出生效。
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getBrand, saveBrand, resetBrand } from '../api'

const fontsZh = ['微软雅黑', '思源黑体', '苹方', '宋体', '楷体', 'Noto Sans CJK SC']
const fontsEn = ['Arial', 'Calibri', 'Helvetica', 'Roboto', 'Segoe UI']

const colorKeys   = ['primary','secondary','accent','warn','neutral','text','text_on_primary']
const colorLabels = {
  primary:'主色 Primary', secondary:'辅色 Secondary', accent:'强调 Accent',
  warn:'警示 Warn', neutral:'中性 Neutral', text:'正文 Text',
  text_on_primary:'主色底文字 Text-on-Primary',
}
const colorHints = {
  primary:'表头背景、KPI', secondary:'分组表头、次级标题',
  accent:'要因=是、关键节点', warn:'AI 补全标记、注意',
  neutral:'边框、分隔线', text:'正文黑', text_on_primary:'主色底上的文字',
}

const form = reactive({
  name:'', company:'',
  primary:'0F172A', secondary:'1E3A8A', accent:'DC2626', warn:'F59E0B',
  neutral:'E5E7EB', text:'0F172A', text_on_primary:'FFFFFF',
  font_zh:'微软雅黑', font_en:'Arial', header_style:'solid',
})
const presets = ref({})
const saving = ref(false)

function toHex(v) { return (v || '').replace('#','').toUpperCase() }

function hexToRgb(h) {
  const x = toHex(h).padEnd(6, '0')
  return [parseInt(x.slice(0,2),16), parseInt(x.slice(2,4),16), parseInt(x.slice(4,6),16)]
}
function rgbToHex(r, g, b) {
  const clamp = (n) => Math.max(0, Math.min(255, Number(n) || 0))
  const hex = (n) => clamp(n).toString(16).padStart(2,'0').toUpperCase()
  return `${hex(r)}${hex(g)}${hex(b)}`
}

async function load() {
  const r = await getBrand()
  Object.assign(form, r.current)
  presets.value = r.presets
}
onMounted(load)

function applyPreset(k) {
  const p = presets.value[k]
  if (!p) return
  Object.assign(form, p)
  ElMessage.success(`已应用预设：${p.name}`)
}

async function save() {
  saving.value = true
  try {
    const payload = { ...form }
    for (const k of colorKeys) payload[k] = toHex(payload[k])
    await saveBrand(payload)
    ElMessage.success('已保存，导出立即生效')
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  } finally { saving.value = false }
}

async function reload() {
  try {
    const r = await resetBrand('default')
    Object.assign(form, r.current)
    ElMessage.success('已重置为默认预设')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

// —— 预览样式 —— //
const previewShellStyle = computed(() => ({
  background: '#fff', border: `1px solid #${form.neutral}`,
  borderRadius: '8px', padding: '14px', fontFamily: form.font_zh,
}))
const previewTitleStyle = computed(() => ({
  background: `#${form.primary}`, color: `#${form.text_on_primary}`,
  padding: '10px 14px', fontSize: '16px', fontWeight: 700, borderRadius: '4px',
}))
const previewCompany = form.company
const thStyle = computed(() => ({
  background: `#${form.primary}`, color: `#${form.text_on_primary}`,
  padding: '8px 10px', fontWeight: 600, textAlign: 'left',
  border: `1px solid #${form.neutral}`,
}))
const th2Style = computed(() => ({ ...thStyle.value, background: `#${form.secondary}` }))
const previewTableStyle = computed(() => ({
  width: '100%', borderCollapse: 'collapse', marginTop: '10px',
  fontSize: '12.5px', color: `#${form.text}`,
}))
const idxStyle = computed(() => ({
  background: mix(form.neutral, 'FFFFFF', 0.5),
  padding: '6px 10px', textAlign: 'center', fontWeight: 600,
  border: `1px solid #${form.neutral}`,
}))
const keyStyle = computed(() => ({
  background: mix(form.secondary, 'FFFFFF', 0.85),
  color: `#${form.secondary}`, fontWeight: 600,
  padding: '6px 10px', border: `1px solid #${form.neutral}`,
}))
const plainStyle = computed(() => ({
  padding: '6px 10px', border: `1px solid #${form.neutral}`,
}))
const aiStyle = computed(() => ({
  background: mix(form.warn, 'FFFFFF', 0.9),
  color: darken(form.warn), padding: '6px 10px',
  border: `1px solid #${form.neutral}`,
}))
const accentStyle = computed(() => ({
  background: `#${form.accent}`, color: '#fff', fontWeight: 700,
  padding: '6px 10px', textAlign: 'center',
  border: `1px solid #${form.neutral}`,
}))
const mutedStyle = computed(() => ({
  background: mix(form.neutral, 'FFFFFF', 0.4),
  color: `#${form.text}`, padding: '6px 10px', textAlign: 'center',
  border: `1px solid #${form.neutral}`,
}))

function mix(a, b, t) {
  const rgb = (h) => [parseInt(h.slice(0,2),16), parseInt(h.slice(2,4),16), parseInt(h.slice(4,6),16)]
  const [ar,ag,ab] = rgb(toHex(a)); const [br,bg,bb] = rgb(toHex(b))
  const hex = (n) => n.toString(16).padStart(2,'0')
  const to = (x,y) => Math.round(x + (y-x)*t)
  return `#${hex(to(ar,br))}${hex(to(ag,bg))}${hex(to(ab,bb))}`
}
function darken(h) {
  const rgb = (x) => parseInt(x,16)
  const dr = Math.round(rgb(h.slice(0,2))*0.65)
  const dg = Math.round(rgb(h.slice(2,4))*0.65)
  const db = Math.round(rgb(h.slice(4,6))*0.65)
  const hex = (n) => n.toString(16).padStart(2,'0')
  return `#${hex(dr)}${hex(dg)}${hex(db)}`
}

// —— 预览样式 —— //
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
.qc-panel-hd { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 12px; }
.tip-bar {
  background: #f5f3ff; color: #5b21b6; padding: 8px 12px;
  border-radius: 6px; font-size: 12.5px;
  border-left: 3px solid #7c3aed;
}

.preset-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.preset-card {
  border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px;
  cursor: pointer; transition: all .15s;
}
.preset-card:hover { border-color: #7c3aed; transform: translateY(-1px); }
.swatches { display: flex; gap: 4px; margin-bottom: 6px; }
.swatches span {
  display: inline-block; width: 100%; height: 22px; border-radius: 3px;
}
.preset-name { font-size: 12.5px; color: #334155; font-weight: 500; }

.preview-shell { min-height: 300px; }
.preview-company { text-align: right; color: #64748b; font-size: 11px; font-style: italic; margin-top: 4px; }
.preview-table th, .preview-table td { line-height: 1.5; }
.preview-legend {
  display: flex; gap: 14px; margin-top: 12px; font-size: 12px; color: #475569;
  flex-wrap: wrap;
}
.preview-legend span {
  display: inline-block; width: 14px; height: 14px; border-radius: 3px;
  margin-right: 4px; vertical-align: -3px;
}

:deep(.hex-input) {
  width: 78px; padding: 4px 8px; border: 1px solid #e5e7eb;
  border-radius: 4px; font-family: ui-monospace, monospace;
  text-transform: uppercase; letter-spacing: 1px;
}
.color-row {
  display: flex; gap: 6px; align-items: center;
  width: 100%; flex-wrap: wrap;
}
.hex-prefix { color: #94a3b8; font-family: ui-monospace, monospace; }
.rgb-sep { color: #94a3b8; font-size: 11px; margin-left: 4px; font-weight: 600; }
.rgb-input {
  width: 52px; padding: 4px 6px; border: 1px solid #e5e7eb;
  border-radius: 4px; font-family: ui-monospace, monospace; text-align: center;
}
.rgb-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.color-hint { color: #94a3b8; font-size: 12px; margin-left: 6px; }
</style>

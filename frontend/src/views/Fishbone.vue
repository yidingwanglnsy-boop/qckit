<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#0ea5e9"><Share /></el-icon>
        <div>
          <div class="tb-title">鱼骨图（Fishbone / Ishikawa · 4M）</div>
          <div class="tb-sub">自动 人/机/料/法 分类，末端不足时 LLM 联想补齐；支持 1-3 层</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button size="default" :disabled="!hasResult" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button size="default" :disabled="!hasResult" @click="exportSvg">
          <el-icon><Picture /></el-icon>&nbsp;SVG
        </el-button>
        <el-button size="default" type="primary" :disabled="!hasResult"
          :loading="pptxLoading" @click="exportPptx">
          <el-icon><Document /></el-icon>&nbsp;PPTX
        </el-button>
      </div>
    </div>

    <el-row :gutter="14">
      <el-col :md="8" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">📝 输入</div>
          <el-form label-position="top" size="default">
            <el-form-item label="鱼头（问题 / 结果）">
              <el-input v-model="topic" placeholder="如：焊接工序不良率偏高" />
            </el-form-item>
            <el-form-item label="背景（可选）">
              <el-input v-model="context" type="textarea" :rows="2" resize="none"
                placeholder="如：3 号机台近 2 周不良率从 1.2% 升至 3.5%" />
            </el-form-item>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="每类目标条数">
                  <el-input-number v-model="target" :min="1" :max="10" style="width:100%;" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="鱼骨层数">
                  <el-radio-group v-model="layers">
                    <el-radio-button :value="1">1 层</el-radio-button>
                    <el-radio-button :value="2">2 层</el-radio-button>
                    <el-radio-button :value="3">3 层</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="已有末端原因（每行一条，可空）">
              <el-input v-model="causesText" type="textarea" :rows="6"
                placeholder="焊工技能参差不齐&#10;保护气流量表偏差&#10;（留空则完全由 AI 生成）" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="loading" @click="run" style="width:100%;">
            <el-icon><MagicStick /></el-icon>&nbsp;
            {{ hasResult ? '重新生成' : 'AI 分类 + 补全' }}
          </el-button>
          <transition name="fade">
            <div v-if="loading" style="margin-top:10px;">
              <el-progress :percentage="Math.round(progress)" :stroke-width="6" :show-text="false" />
              <div style="text-align:center;color:#94a3b8;font-size:12px;margin-top:4px;">
                AI 推理中… <span class="mono">{{ elapsed }}s</span>
              </div>
            </div>
          </transition>
        </div>

        <transition name="fade">
          <div class="qc-panel" v-if="reasoning">
            <div class="qc-panel-hd">🤖 推理</div>
            <div class="summary-text">{{ reasoning }}</div>
          </div>
        </transition>
      </el-col>

      <el-col :md="16" :xs="24">
        <div class="qc-panel" style="padding:8px;">
          <div class="qc-panel-hd" style="padding:6px 10px;">🐟 鱼骨图</div>
          <div class="svg-wrap" ref="svgWrap">
            <svg v-if="hasResult" :viewBox="`0 0 ${W} ${H}`" xmlns="http://www.w3.org/2000/svg"
                 class="fish-svg">
              <!-- 主脊 -->
              <line :x1="20" :y1="H/2" :x2="W-160" :y2="H/2"
                    :stroke="C.text" stroke-width="3" />
              <!-- 箭头 -->
              <polygon :points="`${W-160},${H/2-8} ${W-140},${H/2} ${W-160},${H/2+8}`"
                       :fill="C.text" />
              <!-- 鱼头 -->
              <rect :x="W-140" :y="H/2-30" width="130" height="60" rx="8"
                    :fill="C.primary" :stroke="C.primary" />
              <text :x="W-75" :y="H/2+5" text-anchor="middle" fill="#fff"
                    font-weight="700" font-size="15">{{ topic }}</text>

              <!-- 4 根大骨 -->
              <g v-for="(cat, idx) in categories" :key="cat.category">
                <line v-bind="boneCoords(idx)"
                      :stroke="C.secondary" stroke-width="2.5" />
                <rect v-bind="labelRect(idx)" rx="4"
                      :fill="C.secondary" :stroke="C.secondary" />
                <text v-bind="labelText(idx)" text-anchor="middle"
                      fill="#fff" font-weight="700" font-size="13">
                  {{ cat.name }}
                </text>
                <!-- 中骨/末端 -->
                <g v-for="(sub, si) in cat.children" :key="si">
                  <template v-if="layers === 1">
                    <line v-bind="tipCoords(idx, si, cat.children.length)"
                          :stroke="C.neutralDark" stroke-width="1.5" />
                    <text v-bind="tipText(idx, si, cat.children.length)"
                          :fill="sub.inferred ? C.warnText : C.text"
                          font-size="11" font-weight="500">
                      {{ sub.name }}
                    </text>
                  </template>
                  <template v-else>
                    <line v-bind="midBoneCoords(idx, si, cat.children.length)"
                          :stroke="C.neutralDark" stroke-width="1.8" />
                    <text v-bind="midBoneText(idx, si, cat.children.length)"
                          :fill="sub.inferred ? C.warnText : C.secondary"
                          font-size="12" font-weight="600">
                      {{ sub.name }}
                    </text>
                    <!-- 层 3: 末端小骨 -->
                    <g v-if="layers === 3" v-for="(leaf, li) in sub.children" :key="li">
                      <line v-bind="leafCoords(idx, si, li, cat.children.length, sub.children.length)"
                            :stroke="C.neutral" stroke-width="1" />
                      <text v-bind="leafText(idx, si, li, cat.children.length, sub.children.length)"
                            :fill="leaf.inferred ? C.warnText : C.text"
                            font-size="10">
                        {{ leaf.name }}
                      </text>
                    </g>
                  </template>
                </g>
              </g>
            </svg>
            <div v-else class="placeholder">
              <el-icon :size="42" color="#cbd5e1"><Share /></el-icon>
              <div style="margin-top:8px;">填写主题后点 "AI 分类 + 补全"</div>
            </div>
          </div>
        </div>

        <div v-if="hasResult" class="qc-panel">
          <div class="qc-panel-hd">
            📋 末端原因清单（可编辑，改动即时刷新鱼骨图）
            <span style="color:#94a3b8;font-weight:400;margin-left:8px;font-size:12px;">
              左侧橙色条 = AI 补全
            </span>
          </div>
          <div class="cat-grid">
            <div v-for="cat in categories" :key="cat.category" class="cat-card">
              <div class="cat-hd" :style="`background:#${brand.secondary}`">
                <span>{{ cat.name }} · {{ leafCount(cat) }}</span>
                <el-button link size="small" style="color:#fff;"
                  @click="addLeaf(cat)">
                  <el-icon><Plus /></el-icon>&nbsp;加一条
                </el-button>
              </div>
              <ul>
                <li v-for="leaf in flatten(cat.children)" :key="leaf.uid"
                    :class="{ 'ai': leaf.node.inferred }">
                  <span class="path">{{ leaf.path }}</span>
                  <el-input v-model="leaf.node.name" size="small"
                    @change="leaf.node.inferred = false"
                    class="leaf-input" />
                  <el-icon class="del" @click="removeLeaf(cat, leaf.node)"><Close /></el-icon>
                </li>
                <li v-if="cat.children.length === 0" class="empty">
                  （空，点右上"加一条"）
                </li>
              </ul>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { analyzeFishbone, downloadPptx, getBrand } from '../api'

const topic = ref('')
const context = ref('')
const causesText = ref('')
const target = ref(4)
const layers = ref(2)

const categories = ref([])
const reasoning = ref('')
const loading = ref(false)
const pptxLoading = ref(false)
const progress = ref(0); const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

const brand = reactive({
  primary:'0F172A', secondary:'1E3A8A', accent:'DC2626',
  warn:'F59E0B', neutral:'E5E7EB', text:'0F172A',
})
onMounted(async () => {
  try { const r = await getBrand(); Object.assign(brand, r.current) } catch {}
})

const C = computed(() => ({
  primary: '#' + brand.primary,
  secondary: '#' + brand.secondary,
  accent: '#' + brand.accent,
  warn: '#' + brand.warn,
  warnText: darken(brand.warn),
  neutral: '#' + brand.neutral,
  neutralDark: darken(brand.neutral, 0.25),
  text: '#' + brand.text,
}))

function darken(h, k=0.4) {
  const r=parseInt(h.slice(0,2),16), g=parseInt(h.slice(2,4),16), b=parseInt(h.slice(4,6),16)
  const dx=(x)=>Math.max(0,Math.round(x*(1-k))).toString(16).padStart(2,'0')
  return `#${dx(r)}${dx(g)}${dx(b)}`
}

const hasResult = computed(() => categories.value.length > 0)

// —— SVG 坐标计算 —— //
const W = 900, H = 520
const CX = W - 140       // 鱼头左端
const centerY = H / 2
const boneStartX = 60    // 第一根大骨的锚点起始
const boneSpan = CX - boneStartX - 40  // 4 根均分的横向跨度

function boneCoords(idx) {
  // idx 0/1 在上方向鱼头方向倾斜; 2/3 在下方向鱼头方向倾斜
  const up = idx % 2 === 0
  const half = Math.floor(idx / 2)          // 0 或 1: 大骨在左还是右列
  const anchorX = boneStartX + half * (boneSpan / 2) + 80
  const y1 = up ? 40 : H - 40
  const spineX = anchorX + (up ? 90 : 90)   // 大骨在主脊上落点
  return { x1: anchorX, y1, x2: spineX, y2: centerY }
}
function labelRect(idx) {
  const up = idx % 2 === 0
  const half = Math.floor(idx / 2)
  const anchorX = boneStartX + half * (boneSpan / 2) + 80
  const y = up ? 10 : H - 40
  return { x: anchorX - 45, y, width: 90, height: 30 }
}
function labelText(idx) {
  const up = idx % 2 === 0
  const half = Math.floor(idx / 2)
  const anchorX = boneStartX + half * (boneSpan / 2) + 80
  const y = up ? 30 : H - 20
  return { x: anchorX, y }
}
// 层 1: 直接把末端小骨挂到大骨上
function tipCoords(idx, si, n) {
  const b = boneCoords(idx)
  const up = idx % 2 === 0
  const t = (si + 1) / (n + 1)              // 0..1 沿大骨方向
  const x = b.x1 + (b.x2 - b.x1) * t
  const y = b.y1 + (b.y2 - b.y1) * t
  const dir = up ? 1 : -1                   // 小骨往斜下/斜上
  return { x1: x, y1: y, x2: x + 26, y2: y + dir * 8 }
}
function tipText(idx, si, n) {
  const c = tipCoords(idx, si, n)
  return { x: c.x2 + 4, y: c.y2 + 4 }
}
// 层 2/3: 中骨（水平指向大骨方向）
function midBoneCoords(idx, si, n) {
  const b = boneCoords(idx)
  const up = idx % 2 === 0
  const t = (si + 1) / (n + 1)
  const x = b.x1 + (b.x2 - b.x1) * t
  const y = b.y1 + (b.y2 - b.y1) * t
  return { x1: x - 55, y1: y, x2: x, y2: y }
}
function midBoneText(idx, si, n) {
  const c = midBoneCoords(idx, si, n)
  return { x: c.x1 - 2, y: c.y1 - 3, 'text-anchor': 'end' }
}
// 层 3: 末端叶子（挂在中骨上，短斜线）
function leafCoords(idx, si, li, n, ln) {
  const m = midBoneCoords(idx, si, n)
  const up = idx % 2 === 0
  const t = (li + 1) / (ln + 1)
  const x = m.x1 + (m.x2 - m.x1) * t
  const y = m.y1
  const dir = up ? -1 : 1
  return { x1: x, y1: y, x2: x - 18, y2: y + dir * 10 }
}
function leafText(idx, si, li, n, ln) {
  const c = leafCoords(idx, si, li, n, ln)
  return { x: c.x2 - 3, y: c.y2 + 3, 'text-anchor': 'end' }
}

// —— 树形辅助 —— //
function leafCount(cat) {
  let n = 0
  const walk = (arr) => arr.forEach(x => x.children?.length ? walk(x.children) : n++)
  walk(cat.children); return n
}
function flatten(nodes, prefix = '', out = null, ctr = null) {
  out = out || []
  ctr = ctr || { i: 0 }
  nodes.forEach(n => {
    const path = prefix ? `${prefix} › ` : ''
    if (n.children && n.children.length)
      flatten(n.children, `${path}${n.name}`, out, ctr)
    else
      out.push({ uid: ctr.i++, node: n, path })
  })
  return out
}

function addLeaf(cat) {
  // 层 1: 直接挂到 cat.children; 层 2/3: 挂到第一个子类下（没有则建一个"其它"）
  if (layers.value === 1) {
    cat.children.push({ name: '新末端原因', inferred: false, children: [] })
  } else {
    if (cat.children.length === 0)
      cat.children.push({ name: '其它', inferred: false, children: [] })
    const sub = cat.children[0]
    if (layers.value === 2) {
      // 层 2: 中骨即末端，直接加一条同级中骨
      cat.children.push({ name: '新末端原因', inferred: false, children: [] })
    } else {
      // 层 3: 末端挂在子类下
      sub.children = sub.children || []
      sub.children.push({ name: '新末端原因', inferred: false, children: [] })
    }
  }
}

function removeLeaf(cat, target) {
  const walk = (nodes) => {
    const i = nodes.indexOf(target)
    if (i >= 0) { nodes.splice(i, 1); return true }
    return nodes.some(n => n.children && walk(n.children))
  }
  walk(cat.children)
  // 清理空子类
  cat.children = cat.children.filter(n => !n.children || n.children.length > 0 || layers.value !== 3)
}

// —— 执行 —— //
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
  if (!topic.value.trim()) return ElMessage.warning('请填写鱼头（主题）')
  loading.value = true; startProgress()
  try {
    const causes = causesText.value
      .split(/\r?\n/).map(s => s.trim()).filter(s => s.length >= 2)
    const resp = await analyzeFishbone({
      topic: topic.value,
      context: context.value,
      causes,
      target_per_category: target.value,
      layers: layers.value,
    })
    categories.value = resp.categories
    reasoning.value = resp.reasoning
    stopProgress()
    ElMessage.success('已生成')
  } catch (e) {
    stopProgress()
    ElMessage.error(e.response?.data?.detail || e.message || '失败')
  } finally {
    setTimeout(() => { loading.value = false }, 300)
  }
}

function exportJson() {
  const payload = { topic: topic.value, context: context.value,
                    layers: layers.value, categories: categories.value,
                    reasoning: reasoning.value }
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `鱼骨图_${topic.value}.json`; a.click()
}

function exportSvg() {
  const svg = document.querySelector('.fish-svg')
  if (!svg) return
  const src = new XMLSerializer().serializeToString(svg)
  const blob = new Blob([src], { type: 'image/svg+xml' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `鱼骨图_${topic.value}.svg`; a.click()
}

async function exportPptx() {
  pptxLoading.value = true
  try {
    const payload = { topic: topic.value, context: context.value,
                      layers: layers.value, categories: categories.value,
                      reasoning: reasoning.value }
    await downloadPptx('fishbone', payload, `鱼骨图_${topic.value}.pptx`)
    ElMessage.success('PPTX 已下载（PPT 里可点选每根骨、每段文字编辑）')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
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
.tb-sub { font-size: 12px; color: #64748b; margin-top: 2px; }
.tb-right { display: flex; gap: 8px; }

.qc-panel {
  background: #fff; border-radius: 10px; padding: 16px 18px;
  margin-bottom: 12px; border: 1px solid #eef2f7;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.qc-panel-hd { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 12px; }
.summary-text {
  color: #451a03; line-height: 1.75; font-size: 13px;
  background: #fffbeb; padding: 12px 14px; border-radius: 6px;
  border-left: 3px solid #f59e0b;
}
.svg-wrap { min-height: 520px; display: flex; align-items: center; justify-content: center; }
.fish-svg { width: 100%; height: auto; max-height: 620px; }
.placeholder {
  color: #94a3b8; font-size: 13px; text-align: center;
  padding: 60px 20px;
}
.cat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.cat-card { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.cat-hd {
  color: #fff; padding: 6px 12px; font-weight: 700; font-size: 13px;
  display: flex; justify-content: space-between; align-items: center;
}
.cat-card ul { list-style: none; padding: 6px 10px; margin: 0; }
.cat-card li {
  padding: 4px 0; font-size: 12.5px; color: #334155;
  display: flex; gap: 6px; align-items: center;
  border-left: 3px solid transparent; padding-left: 6px;
}
.cat-card li.ai { border-left-color: #f59e0b; background: #fffbeb; }
.cat-card li.empty {
  justify-content: center; color: #cbd5e1; font-size: 12px; padding: 12px 0;
}
.cat-card .path { color: #94a3b8; font-size: 11px; min-width: 0; flex-shrink: 0; }
.cat-card .leaf-input { flex: 1; }
.cat-card .del { color: #cbd5e1; cursor: pointer; }
.cat-card .del:hover { color: #dc2626; }
.mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; }
.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

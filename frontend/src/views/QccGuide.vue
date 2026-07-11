<template>
  <div class="qc-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#0891b2"><Guide /></el-icon>
        <div>
          <div class="tb-title">QCC 思路生成器（Problem-Solving QCC Roadmap）</div>
          <div class="tb-sub">面向新手：问题解决型 QCC 五阶段思路 + 每阶段推荐工具、使用建议、常见陷阱</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button :disabled="!hasResult" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button :disabled="!hasResult" @click="exportMd">
          <el-icon><Document /></el-icon>&nbsp;Markdown
        </el-button>
      </div>
    </div>

    <el-row :gutter="14">
      <el-col :md="7" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">📝 输入</div>
          <el-form label-position="top" size="default">
            <el-form-item label="课题（可空，空则出通用示例）">
              <el-input v-model="topic" placeholder="如：某工序不良率偏高" />
            </el-form-item>
            <el-form-item label="行业（可选）">
              <el-input v-model="industry" placeholder="如：焊接 / 注塑 / 装配" />
            </el-form-item>
            <el-form-item label="经验级别">
              <el-radio-group v-model="experience">
                <el-radio-button value="新手">新手</el-radio-button>
                <el-radio-button value="熟悉">熟悉</el-radio-button>
                <el-radio-button value="资深">资深</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="额外偏好（可选）">
              <el-input v-model="focus" type="textarea" :rows="2" resize="none"
                placeholder="如：重点讲根因分析 / 讲一下如何选课题" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="loading" @click="run" style="width:100%;">
            <el-icon><MagicStick /></el-icon>&nbsp;
            {{ hasResult ? '重新生成思路' : 'AI 生成 QCC 思路' }}
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
          <div class="qc-panel" v-if="overview">
            <div class="qc-panel-hd">🧭 整体思路</div>
            <div class="overview-text">{{ overview }}</div>
          </div>
        </transition>
      </el-col>

      <el-col :md="17" :xs="24">
        <div class="qc-panel" v-if="!hasResult" style="text-align:center;padding:60px 20px;">
          <el-icon :size="48" color="#cbd5e1"><Guide /></el-icon>
          <div style="color:#94a3b8;margin-top:12px;">填写课题（或直接留空），点左侧按钮生成五阶段思路</div>
        </div>

        <div v-for="(s, i) in stages" :key="s.id" class="stage-card">
          <div class="stage-hd">
            <div class="stage-num" :style="`background:#${brand.primary}`">{{ i + 1 }}</div>
            <div style="flex:1;">
              <div class="stage-title">{{ s.title }}</div>
              <div class="stage-goal">🎯 {{ s.goal }}</div>
            </div>
          </div>
          <div class="stage-body">
            <div class="col-block">
              <div class="col-hd" :style="`color:#${brand.secondary}`">📌 关键动作</div>
              <ol>
                <li v-for="(a, j) in s.actions" :key="j">{{ a }}</li>
              </ol>
            </div>
            <div class="col-block">
              <div class="col-hd" :style="`color:#${brand.secondary}`">🛠 推荐工具</div>
              <div class="tools">
                <div v-for="(t, j) in s.tools" :key="j" class="tool-chip">
                  <div class="tool-hd">
                    <span class="tool-name">{{ t.name }}</span>
                    <router-link v-if="t.route" :to="t.route" class="tool-jump">
                      打开 →
                    </router-link>
                  </div>
                  <div class="tool-why">{{ t.why }}</div>
                </div>
              </div>
            </div>
            <div class="col-block">
              <div class="col-hd tip">💡 使用建议</div>
              <ul class="tips">
                <li v-for="(t, j) in s.tips" :key="j">{{ t }}</li>
              </ul>
              <div class="col-hd pit" style="margin-top:10px;">⚠️ 常见陷阱</div>
              <ul class="pitfalls">
                <li v-for="(p, j) in s.pitfalls" :key="j">{{ p }}</li>
              </ul>
            </div>
          </div>
        </div>
        <NextStepBar v-if="hasResult" :from="'qcc_guide'" :topic="topic || ''" />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { analyzeQccGuide, getBrand } from '../api'
import { tryAttachToProject } from '../composables/useAttach'
import NextStepBar from '../components/NextStepBar.vue'

const topic = ref('')
const industry = ref('')
const experience = ref('新手')
const focus = ref('')

const stages = ref([])
const overview = ref('')
const loading = ref(false)
const progress = ref(0); const elapsed = ref(0)
let progressTimer = null, elapsedTimer = null

const brand = reactive({ primary: '0F172A', secondary: '1E3A8A' })
onMounted(async () => {
  try { const r = await getBrand(); Object.assign(brand, r.current) } catch {}
})

const hasResult = computed(() => stages.value.length > 0)

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
  loading.value = true; startProgress()
  try {
    const resp = await analyzeQccGuide({
      topic: topic.value, industry: industry.value,
      experience: experience.value, focus: focus.value,
    })
    stages.value = resp.stages
    overview.value = resp.overview
    stopProgress()
    await tryAttachToProject('qcc_guide', {
      topic: topic.value, industry: industry.value,
      experience: experience.value, focus: focus.value,
    }, resp)
    ElMessage.success('已生成')
  } catch (e) {
    stopProgress()
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally { setTimeout(() => loading.value = false, 300) }
}

function exportJson() {
  const payload = { topic: topic.value, overview: overview.value, stages: stages.value }
  const blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `QCC思路_${topic.value || '通用'}.json`; a.click()
}

function exportMd() {
  const lines = [`# QCC 思路 · ${topic.value || '通用'}`, '', `> ${overview.value}`, '']
  stages.value.forEach((s, i) => {
    lines.push(`## ${i + 1}. ${s.title}`, '', `**目标**: ${s.goal}`, '')
    if (s.actions.length) {
      lines.push('**关键动作**:', ...s.actions.map(a => `- ${a}`), '')
    }
    if (s.tools.length) {
      lines.push('**推荐工具**:')
      s.tools.forEach(t => lines.push(`- **${t.name}** — ${t.why}`))
      lines.push('')
    }
    if (s.tips.length) {
      lines.push('**使用建议**:', ...s.tips.map(t => `- ${t}`), '')
    }
    if (s.pitfalls.length) {
      lines.push('**常见陷阱**:', ...s.pitfalls.map(p => `- ${p}`), '')
    }
  })
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = `QCC思路_${topic.value || '通用'}.md`; a.click()
}

onBeforeUnmount(() => { clearInterval(progressTimer); clearInterval(elapsedTimer) })

// 从 URL query 自动填入 topic (工具间跳转时透传)
const route = useRoute()
onMounted(() => {
  const q = route.query.topic
  if (q && !topic.value) {
    topic.value = String(q)
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
  background: #fff; border-radius: 10px; padding: 16px 18px;
  margin-bottom: 12px; border: 1px solid #eef2f7;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.qc-panel-hd { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 12px; }
.overview-text {
  color: #075985; line-height: 1.75; font-size: 13px;
  background: #f0f9ff; padding: 12px 14px; border-radius: 6px;
  border-left: 3px solid #0891b2;
}

.stage-card {
  background: #fff; border-radius: 10px; padding: 16px 18px;
  margin-bottom: 12px; border: 1px solid #eef2f7;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.stage-hd { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 14px; }
.stage-num {
  color: #fff; width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 15px; flex-shrink: 0;
}
.stage-title { font-size: 15px; font-weight: 700; color: #0f172a; }
.stage-goal { font-size: 12.5px; color: #475569; margin-top: 4px; line-height: 1.6; }

.stage-body {
  display: grid; grid-template-columns: 1.2fr 1.4fr 1.2fr; gap: 16px;
}
@media (max-width: 900px) { .stage-body { grid-template-columns: 1fr; } }
.col-block { min-width: 0; }
.col-hd { font-size: 12.5px; font-weight: 600; margin-bottom: 6px; }
.col-hd.tip { color: #b45309; }
.col-hd.pit { color: #b91c1c; }
.col-block ol, .col-block ul {
  margin: 0; padding-left: 20px; color: #334155;
  font-size: 12.5px; line-height: 1.75;
}
.tools { display: flex; flex-direction: column; gap: 8px; }
.tool-chip {
  background: #f8fafc; border-radius: 6px; padding: 8px 10px;
  border-left: 3px solid #94a3b8;
}
.tool-hd {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12.5px; font-weight: 600; color: #0f172a; margin-bottom: 3px;
}
.tool-jump {
  color: #7c3aed; font-size: 11.5px; text-decoration: none; font-weight: 500;
}
.tool-jump:hover { text-decoration: underline; }
.tool-why { color: #64748b; font-size: 11.5px; line-height: 1.55; }

.tips li { color: #78350f; }
.pitfalls li { color: #7f1d1d; }
.mono { font-family: ui-monospace, monospace; }
.fade-enter-active, .fade-leave-active { transition: opacity .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>

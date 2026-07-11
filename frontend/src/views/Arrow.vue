<template>
  <ToolPage
    tool-key="arrow" title="箭线图（Arrow Diagram / CPM）" icon-name="Right"
    subtitle="任务排期 + 关键路径 · LLM 推断依赖 + PERT 工期估算"
    :form="form" :analyze-fn="doAnalyze"
    :build-payload="(f, r) => r"
    :pptx-filename="f => `箭线图_${f.topic || 'arrow'}.pptx`">
    <template #inputs>
      <el-form label-position="top" size="default">
        <el-form-item label="项目主题">
          <el-input v-model="form.topic" placeholder="如：QCC 项目 12 周计划" />
        </el-form-item>
        <el-row :gutter="8">
          <el-col :span="12">
            <el-form-item label="起始日期">
              <el-date-picker v-model="form.start_date" type="date"
                              value-format="YYYY-MM-DD" style="width:100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="截止日期（可选）">
              <el-date-picker v-model="form.end_date" type="date"
                              value-format="YYYY-MM-DD" style="width:100%;"
                              placeholder="留空按工期自动推算" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="任务清单（每行一个：任务名, 工期天, 前置任务, owner）">
          <el-input v-model="form.tasks_text" type="textarea" :rows="7"
                    placeholder="选题, 3, , 张三&#10;现状调查, 7, 选题, 李四&#10;要因分析, 8, 现状调查, 王五" />
          <div style="font-size:11px;color:#94a3b8;margin-top:2px;">
            💡 工期/前置留空时，AI 会用 PERT 估算并推断依赖
          </div>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.auto_infer">
            AI 自动补全空缺（推荐）
          </el-checkbox>
        </el-form-item>
        <el-form-item label="背景（可选）">
          <el-input v-model="form.context" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </template>

    <template #results="{ result }">
      <div class="result-section" style="background:#fef2f2;">
        <h4 style="color:#b91c1c;">
          🔴 关键路径（总工期 {{ result.project_duration }} 天{{ dateRangeLabel(result) }}）
        </h4>
        <div style="font-family:monospace;">
          {{ (result.critical_path || []).join('  →  ') || '—' }}
        </div>
      </div>

      <div class="result-section">
        <h4>📅 甘特图</h4>
        <div class="gantt">
          <!-- 顶部时间轴 -->
          <div class="gantt-row gantt-axis">
            <div class="task-name" style="font-weight:600;color:#475569;">时间刻度</div>
            <div class="gantt-bar-wrap axis-wrap">
              <div v-for="(tk, i) in ticks(result)" :key="i" class="tick"
                   :style="{ left: tk.pct + '%' }">
                <div class="tick-line"></div>
                <div class="tick-label">{{ tk.label }}</div>
              </div>
            </div>
          </div>
          <!-- 任务行 -->
          <div v-for="t in result.tasks" :key="t.name" class="gantt-row">
            <div class="task-name" :class="{ critical: t.is_critical }">
              {{ t.is_critical ? '🔴' : '' }} {{ t.name }}
              <span style="color:#94a3b8;font-size:11px;">
                ({{ t.duration }}d<span v-if="t.slack > 0">, 浮时 {{ t.slack }}d</span>)
              </span>
            </div>
            <div class="gantt-bar-wrap">
              <!-- 竖网格线 -->
              <div v-for="(tk, i) in ticks(result)" :key="'g'+i"
                   class="grid-v" :style="{ left: tk.pct + '%' }"></div>
              <!-- 任务条 -->
              <div class="gantt-bar" :class="{ critical: t.is_critical }"
                   :style="barStyle(t, result)"
                   :title="taskTooltip(t, result)">
                <span class="bar-txt">{{ barText(t, result) }}</span>
              </div>
              <div v-if="t.slack > 0" class="gantt-slack"
                   :style="slackStyle(t, result)"></div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="result.resource_conflicts?.length" class="result-section">
        <h4>⚙ 资源冲突</h4>
        <ul style="margin:0;padding-left:18px;">
          <li v-for="(c,i) in result.resource_conflicts" :key="i">
            <b>{{ c.owner }}</b>: {{ (c.tasks || []).join(' / ') }} — {{ c.advice }}
          </li>
        </ul>
      </div>
      <div v-if="result.recommendations?.length" class="result-section">
        <h4>💡 优化建议</h4>
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
import { analyzeArrow } from '../api'
import { ElMessage } from 'element-plus'

const form = reactive({
  topic: '', tasks_text: '', auto_infer: true, context: '',
  start_date: '', end_date: '',
})

async function doAnalyze (f) {
  const tasks = f.tasks_text.split('\n').map(line => {
    const parts = line.split(/[,，]/).map(s => s.trim())
    if (!parts[0]) return null
    return {
      name: parts[0],
      duration: parts[1] ? parseFloat(parts[1]) : null,
      predecessors: parts[2] ? parts[2].split(/[;；\s]+/).filter(Boolean) : null,
      owner: parts[3] || null,
    }
  }).filter(Boolean)
  if (tasks.length < 2) {
    ElMessage.warning('请至少填写 2 个任务')
    throw new Error('invalid')
  }
  return await analyzeArrow({
    topic: f.topic, tasks,
    auto_infer: f.auto_infer,
    context: f.context || null,
  })
}

// —— 日期换算 ——————————————————————————————————————
function projectDur (r) {
  // 若指定 end_date, 用日历天数替代 CPM 工期
  if (form.start_date && form.end_date) {
    const d = (new Date(form.end_date) - new Date(form.start_date)) / 86400000
    if (d > 0) return d
  }
  return r.project_duration || 1
}
function dayOffsetToDate (d) {
  if (!form.start_date) return null
  const dt = new Date(form.start_date)
  dt.setDate(dt.getDate() + Math.round(d))
  return dt.toISOString().slice(5, 10)  // MM-DD
}
function dateRangeLabel (r) {
  if (!form.start_date) return ''
  const end = dayOffsetToDate(projectDur(r))
  return ` · ${form.start_date.slice(5)} → ${end}`
}

// —— 时间刻度 ——————————————————————————————————————
function ticks (r) {
  const dur = projectDur(r)
  const n = dur <= 14 ? 7 : dur <= 60 ? 6 : 8
  return Array.from({ length: n + 1 }, (_, i) => {
    const d = (i / n) * dur
    const pct = (i / n) * 100
    return {
      pct,
      label: form.start_date ? dayOffsetToDate(d) : `${d.toFixed(0)}d`,
    }
  })
}

// —— 任务条 ——————————————————————————————————————
function barStyle (t, r) {
  const dur = projectDur(r)
  return `left:${(t.es / dur) * 100}%; width:${(t.duration / dur) * 100}%;`
}
function slackStyle (t, r) {
  const dur = projectDur(r)
  return `left:${(t.ef / dur) * 100}%; width:${(t.slack / dur) * 100}%;`
}
function barText (t, r) {
  if (!form.start_date) return `${t.duration}d`
  return `${dayOffsetToDate(t.es)} ~ ${dayOffsetToDate(t.ef)}`
}
function taskTooltip (t, r) {
  const base = `${t.name} · ${t.duration}d`
  if (!form.start_date) return `${base} · ES=${t.es} EF=${t.ef}`
  return `${base}\n${dayOffsetToDate(t.es)} → ${dayOffsetToDate(t.ef)}`
}
</script>

<style scoped>
.gantt { border: 1px solid #e2e8f0; border-radius: 4px; background: #fff; }
.gantt-row {
  display: grid; grid-template-columns: 200px 1fr;
  border-bottom: 1px solid #f1f5f9;
  align-items: center; min-height: 28px;
}
.gantt-row:last-child { border-bottom: none; }
.gantt-axis { min-height: 30px; background: #f8fafc; }
.task-name { padding: 4px 8px; font-size: 12px; }
.task-name.critical { color: #dc2626; font-weight: 600; }

.gantt-bar-wrap { position: relative; height: 22px; overflow: visible; }
.axis-wrap { height: 30px; }

/* 时间刻度 */
.tick { position: absolute; top: 0; height: 100%; transform: translateX(-50%); }
.tick-line { width: 1px; height: 6px; background: #94a3b8; margin: 0 auto; }
.tick-label {
  font-size: 10px; color: #64748b; margin-top: 2px; white-space: nowrap;
  text-align: center;
}

/* 竖网格线 */
.grid-v {
  position: absolute; top: 0; bottom: 0; width: 1px;
  background: #f1f5f9; pointer-events: none;
}

/* 任务条 */
.gantt-bar {
  position: absolute; top: 3px; height: 16px;
  background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
  border-radius: 3px; color: #fff; font-size: 10px;
  line-height: 16px; white-space: nowrap; overflow: hidden;
  padding: 0 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}
.gantt-bar.critical {
  background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%);
}
.bar-txt { display: inline-block; }
.gantt-slack {
  position: absolute; top: 8px; height: 6px;
  background: repeating-linear-gradient(45deg,
    #cbd5e1 0 4px, #e2e8f0 4px 8px);
  border-radius: 2px;
}
</style>

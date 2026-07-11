<template>
  <div class="history-page">
    <div class="page-hd">
      <div>
        <h2 style="margin:0;">📚 分析历史</h2>
        <div class="sub">最近 10 条 / 工具 · 存于浏览器本地 · 可一键恢复继续</div>
      </div>
      <el-button v-if="hasAny" size="default" @click="clearAll">
        <el-icon><Delete /></el-icon>&nbsp;清空全部
      </el-button>
    </div>

    <el-empty v-if="!hasAny" description="暂无历史 · 完成分析后会自动保存" />

    <div v-for="g in groups" :key="g.tool" class="tool-group">
      <div class="tool-hd">
        <el-icon><Grid /></el-icon>
        <b>{{ g.name }}</b>
        <span class="cnt">{{ g.items.length }} 条</span>
      </div>
      <div v-for="h in g.items" :key="h.id" class="hist-row">
        <div class="hist-main">
          <div class="hist-title">{{ h.title }}</div>
          <div class="hist-preview">{{ h.resultPreview || '(无摘要)' }}</div>
          <div class="hist-time">{{ formatTime(h.at) }}</div>
        </div>
        <div class="hist-actions">
          <el-button size="small" @click="openWith(g.tool, h)">
            <el-icon><View /></el-icon>&nbsp;重开
          </el-button>
          <el-button size="small" @click="dropOne(g.tool, h.id)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, View, Delete, Close } from '@element-plus/icons-vue'

const TOOLS = {
  relations: '关联图', affinity: '亲和图', pareto: '柏拉图', radar: '雷达图',
  w5h2: '5W2H', rca: '根因确认', fishbone: '鱼骨图', qcc_guide: 'QCC 思路生成',
  tree: '系统图', matrix: '矩阵图', mda: '矩阵数据解析', pdpc: 'PDPC', arrow: '箭线图',
}
const PATH = { qcc_guide: '/tools/qcc-guide' }

const version = ref(0)  // 用于强制刷新
const groups = computed(() => {
  version.value  // 依赖
  const out = []
  for (const [tool, name] of Object.entries(TOOLS)) {
    try {
      const raw = localStorage.getItem('qckit.history.' + tool)
      if (raw) {
        const items = JSON.parse(raw)
        if (items?.length) out.push({ tool, name, items })
      }
    } catch {}
  }
  return out
})
const hasAny = computed(() => groups.value.length > 0)

const router = useRouter()
function openWith (tool, h) {
  // 把 snapshot 写到"下次要用"的临时槽, ToolPage 读取
  try {
    sessionStorage.setItem('qckit.restore.' + tool, JSON.stringify(h.snapshot))
    router.push(PATH[tool] || `/tools/${tool}`)
  } catch (e) { ElMessage.error('恢复失败') }
}

function dropOne (tool, id) {
  const raw = JSON.parse(localStorage.getItem('qckit.history.' + tool) || '[]')
  localStorage.setItem('qckit.history.' + tool,
    JSON.stringify(raw.filter(x => x.id !== id)))
  version.value++
}

function clearAll () {
  ElMessageBox.confirm('清空所有工具的历史记录？', '确认', {
    confirmButtonText: '清空', cancelButtonText: '取消', type: 'warning',
  }).then(() => {
    for (const k of Object.keys(TOOLS))
      localStorage.removeItem('qckit.history.' + k)
    version.value++
    ElMessage.success('已清空')
  }).catch(() => {})
}

function formatTime (iso) {
  try {
    const d = new Date(iso), now = new Date()
    const diff = (now - d) / 60000
    if (diff < 1) return '刚刚'
    if (diff < 60) return `${Math.floor(diff)} 分钟前`
    if (diff < 1440) return `${Math.floor(diff/60)} 小时前`
    return d.toISOString().slice(0, 16).replace('T', ' ')
  } catch { return iso }
}
</script>

<style scoped>
.history-page { padding: 8px 4px; }
.page-hd {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.sub { font-size: 12px; color: #64748b; margin-top: 4px; }

.tool-group {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  margin-bottom: 12px; overflow: hidden;
}
.tool-hd {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 14px; background: #f8fafc;
  border-bottom: 1px solid #e2e8f0; font-size: 14px;
}
.tool-hd .cnt { color: #94a3b8; font-size: 12px; margin-left: 4px; }

.hist-row {
  display: flex; align-items: center; padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
}
.hist-row:last-child { border-bottom: none; }
.hist-main { flex: 1; min-width: 0; }
.hist-title { font-weight: 500; color: #1e293b; margin-bottom: 2px; }
.hist-preview {
  color: #64748b; font-size: 12px; margin-bottom: 2px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.hist-time { color: #94a3b8; font-size: 11px; }
.hist-actions { display: flex; gap: 6px; flex-shrink: 0; }
</style>

<!--
  ToolkitBar.vue — 通用工具栏, 挂在每个 QC 工具页面顶部
  用法:
    <ToolkitBar :toolkit="tk" />
-->
<template>
  <div class="toolkit-bar">
    <el-dropdown v-if="toolkit.samples.length" @command="toolkit.loadSample">
      <el-button type="primary" plain size="small">
        <el-icon><MagicStick /></el-icon>
        <span style="margin-left:6px">一键填入示例</span>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item v-for="s in toolkit.samples" :key="s.id" :command="s.id">
            📋 {{ s.name }}
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <el-dropdown v-if="toolkit.history.value.length" trigger="click">
      <el-button size="small">
        <el-icon><Clock /></el-icon>
        <span style="margin-left:6px">最近使用 ({{ toolkit.history.value.length }})</span>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="h in toolkit.history.value" :key="h.id"
            @click="toolkit.restoreHistory(h.id)">
            <div style="min-width:260px;padding:2px 0">
              <div style="font-weight:600;color:#1e293b">{{ h.title }}</div>
              <div style="font-size:11px;color:#94a3b8">
                {{ formatTime(h.at) }} · {{ h.resultPreview || '无结论' }}
              </div>
            </div>
          </el-dropdown-item>
          <el-dropdown-item divided @click="toolkit.clearHistory">
            <span style="color:#dc2626">🗑 清空历史</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <span v-else style="font-size:12px;color:#94a3b8;">
      💡 分析成功后会自动保存最近 10 次记录
    </span>
  </div>
</template>

<script setup>
import { MagicStick, Clock } from '@element-plus/icons-vue'
defineProps({ toolkit: { type: Object, required: true } })
function formatTime (iso) {
  const d = new Date(iso)
  const now = Date.now()
  const diff = (now - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff/60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff/3600)} 小时前`
  return `${Math.floor(diff/86400)} 天前`
}
</script>

<style scoped>
.toolkit-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; margin-bottom: 12px;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 6px;
}
</style>

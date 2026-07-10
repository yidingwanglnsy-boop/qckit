<template>
  <div>
    <div class="qc-hero">
      <h1>QCKit · LLM 驱动的质量工具箱</h1>
      <p>让 QC 手法从「填 Excel 模板」升级为「说一句话，直接出图 + 报告」。</p>
    </div>
    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="8" v-for="t in tools" :key="t.key">
        <el-card shadow="hover" class="qc-card" @click="open(t)" style="cursor:pointer;">
          <div style="display:flex;align-items:center;gap:10px;">
            <el-icon size="22" color="#2563eb"><component :is="t.icon || 'Connection'" /></el-icon>
            <b style="font-size:16px;">{{ t.name }}</b>
            <el-tag size="small">{{ t.category }}</el-tag>
          </div>
          <div style="margin-top:8px;color:#6b7280;font-size:13px;line-height:1.6;">
            {{ t.description }}
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-alert
      v-if="!tools.length" type="info" :closable="false"
      title="正在加载工具..." />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listTools } from '../api'

const tools = ref([])
const router = useRouter()

onMounted(async () => { tools.value = await listTools() })
function open(t) { router.push(`/tools/${t.key}`) }
</script>

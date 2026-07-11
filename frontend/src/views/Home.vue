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

    <!-- 首次启动引导 -->
    <el-dialog v-model="showWizard" title="👋 欢迎使用 QCKit"
      width="560px" :close-on-click-modal="false" :show-close="false">
      <div style="line-height:1.8;font-size:14px;">
        <p><strong>1 分钟接入 AI, 开始你的第一个 QCC 分析:</strong></p>
        <ol style="padding-left:20px;margin:12px 0;">
          <li>准备 LLM API Key（推荐 <a href="https://dashscope.aliyun.com" target="_blank">通义千问</a> /
            <a href="https://platform.deepseek.com" target="_blank">DeepSeek</a> —— 都有免费额度）</li>
          <li>点下方【前往设置】，粘贴 Key 并保存</li>
          <li>任选一个工具，点【一键填入示例】看看效果</li>
        </ol>
        <el-alert type="info" :closable="false" show-icon
          style="margin-top:12px;"
          title="没有 Key 也可以先探索界面, 但 AI 分析功能不可用" />
      </div>
      <template #footer>
        <el-button @click="skipWizard">稍后再说</el-button>
        <el-button type="primary" @click="gotoSettings">前往设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listTools, getConfig } from '../api'

const tools = ref([])
const router = useRouter()
const showWizard = ref(false)

onMounted(async () => {
  tools.value = await listTools()
  // 引导条件: 未曾跳过, 且 config 无 api_key
  if (!localStorage.getItem('qckit.wizardSkipped')) {
    try {
      const cfg = await getConfig()
      if (!cfg.llm?.api_key) showWizard.value = true
    } catch {} // 后端未启动就静默
  }
})

function skipWizard () {
  localStorage.setItem('qckit.wizardSkipped', '1')
  showWizard.value = false
}
function gotoSettings () {
  localStorage.setItem('qckit.wizardSkipped', '1')
  showWizard.value = false
  router.push('/settings')
}
function open(t) { router.push(`/tools/${t.key}`) }
</script>

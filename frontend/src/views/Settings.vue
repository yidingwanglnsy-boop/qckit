<template>
  <div class="qc-card" style="max-width:640px;">
    <h2 style="margin-top:0;">LLM 配置</h2>
    <p style="color:#6b7280;">兼容 OpenAI 协议。可接入 DeepSeek、通义千问、Moonshot、本地 vLLM 等。</p>
    <el-form label-width="120px" :model="form">
      <el-form-item label="Base URL">
        <el-input v-model="form.base_url" placeholder="https://api.openai.com/v1" />
      </el-form-item>
      <el-form-item label="API Key">
        <el-input v-model="form.api_key" :placeholder="placeholder" show-password />
      </el-form-item>
      <el-form-item label="Model">
        <el-input v-model="form.model" placeholder="gpt-4o-mini / deepseek-chat / ..." />
      </el-form-item>
      <el-form-item label="Temperature">
        <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, saveConfig } from '../api'

const form = ref({ base_url:'', api_key:'', model:'', temperature:0.2, timeout:120 })
const placeholder = ref('sk-...')
const saving = ref(false)

onMounted(async () => {
  const cfg = await getConfig()
  Object.assign(form.value, cfg.llm)
  if (cfg.llm.api_key) placeholder.value = cfg.llm.api_key // 已掩码
  form.value.api_key = '' // 不显示掩码占位
})

async function save(){
  saving.value = true
  try {
    await saveConfig(form.value)
    ElMessage.success('已保存')
  } catch(e){ ElMessage.error(e.response?.data?.detail || e.message) }
  finally { saving.value = false }
}
</script>

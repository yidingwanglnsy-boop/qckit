<!--
  ToolPage.vue — 新工具通用两栏布局
  Slots:
    #inputs      左侧输入表单
    #results     右侧结果渲染 (result 已注入)
  Props:
    - toolKey       工具 key (samples 用)
    - title         页面标题
    - subtitle      副标题
    - iconName      Element icon 名 (可选)
    - form          reactive form 对象
    - analyzeFn     async (form) => result  的分析函数
    - buildPayload  (form, result) => pptx 导出 payload
    - pptxFilename  下载文件名
-->
<template>
  <div class="tool-page">
    <div class="qc-toolbar">
      <div class="tb-left">
        <el-icon :size="20" color="#2563eb"><component :is="iconName || 'Grid'" /></el-icon>
        <div>
          <div class="tb-title">{{ title }}</div>
          <div class="tb-sub">{{ subtitle }}</div>
        </div>
      </div>
      <div class="tb-right">
        <el-button size="default" :disabled="!result" @click="exportJson">
          <el-icon><Download /></el-icon>&nbsp;JSON
        </el-button>
        <el-button size="default" type="primary" :disabled="!result"
                   :loading="pptxLoading" @click="exportPptx">
          <el-icon><Document /></el-icon>&nbsp;PPTX
        </el-button>
      </div>
    </div>

    <el-row :gutter="14" class="qc-body">
      <el-col :md="10" :xs="24">
        <div class="qc-panel">
          <div class="qc-panel-hd">📝 输入</div>
          <ToolkitBar :toolkit="toolkit" />
          <slot name="inputs" :form="form" />
          <div class="qc-actions">
            <el-button type="primary" size="default"
                       :loading="loading" @click="doAnalyze">
              <el-icon><MagicStick /></el-icon>&nbsp;AI 分析
            </el-button>
            <span v-if="loading" class="qc-progress">分析中…</span>
          </div>
        </div>
      </el-col>

      <el-col :md="14" :xs="24">
        <div class="qc-panel qc-panel-result">
          <div class="qc-panel-hd">📊 结果</div>
          <div v-if="!result" class="qc-empty">
            💡 输入内容后点击「AI 分析」查看结果
          </div>
          <template v-else>
            <slot name="results" :result="result" />
            <NextStepBar :from="toolKey" :topic="form.topic || ''" />
          </template>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, reactive as _r } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, Download, MagicStick } from '@element-plus/icons-vue'
import { downloadPptx } from '../api'
import ToolkitBar from './ToolkitBar.vue'
import NextStepBar from './NextStepBar.vue'
import { useToolkit } from '../composables/useToolkit'
import { tryAttachToProject } from '../composables/useAttach'

const props = defineProps({
  toolKey: String,
  title: String,
  subtitle: String,
  iconName: String,
  form: Object,        // reactive
  analyzeFn: Function,
  buildPayload: Function,   // (form, result) => obj
  pptxFilename: Function,   // (form) => string
})

const loading = ref(false)
const pptxLoading = ref(false)
const result = ref(null)
const toolkit = useToolkit(props.toolKey, props.form)
const route = useRoute()

// 优先级: sessionStorage 恢复 > URL query topic > 空 (不自动填示例)
onMounted(() => {
  const restoreKey = 'qckit.restore.' + props.toolKey
  const raw = sessionStorage.getItem(restoreKey)
  if (raw) {
    try {
      Object.assign(props.form, JSON.parse(raw))
      sessionStorage.removeItem(restoreKey)
      ElMessage.success('已从历史记录恢复')
      return
    } catch {}
  }
  const qtopic = route.query.topic
  if (qtopic && !props.form.topic) {
    props.form.topic = String(qtopic)
    ElMessage.info('已带入上一步的主题，可直接分析')
  }
})

async function doAnalyze () {
  loading.value = true
  try {
    result.value = await props.analyzeFn(props.form)
    toolkit.saveHistory(result.value)
    ElMessage.success('分析完成')
    await tryAttachToProject(props.toolKey, props.form, result.value)
  } catch (e) {
    // 全局拦截器已弹提示
  } finally {
    loading.value = false
  }
}

function exportJson () {
  const blob = new Blob([JSON.stringify(result.value, null, 2)],
    { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = props.pptxFilename(props.form).replace(/\.pptx$/i, '.json')
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 500)
}

async function exportPptx () {
  pptxLoading.value = true
  try {
    const payload = props.buildPayload(props.form, result.value)
    await downloadPptx(props.toolKey, payload, props.pptxFilename(props.form))
  } finally {
    pptxLoading.value = false
  }
}
</script>

<style scoped>
.tool-page { padding: 8px; }
.qc-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; margin-bottom: 12px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
}
.tb-left { display: flex; align-items: center; gap: 12px; }
.tb-title { font-size: 16px; font-weight: 600; color: #1e293b; }
.tb-sub { font-size: 12px; color: #64748b; margin-top: 2px; }
.tb-right { display: flex; gap: 8px; }
.qc-body { min-height: 500px; }
.qc-panel {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 14px; height: 100%; box-sizing: border-box;
}
.qc-panel-hd { font-weight: 600; margin-bottom: 12px; color: #1e293b; }
.qc-actions { margin-top: 12px; display: flex; gap: 12px; align-items: center; }
.qc-progress { color: #64748b; font-size: 12px; }
.qc-empty {
  padding: 60px 20px; text-align: center; color: #94a3b8; font-size: 14px;
}
.qc-panel-result :deep(.result-section) {
  margin-bottom: 14px; padding: 10px 12px;
  background: #f8fafc; border-radius: 6px;
  font-size: 13px; line-height: 1.7;
}
.qc-panel-result :deep(.result-section h4) {
  margin: 0 0 6px; font-size: 13px; color: #1e40af;
}
</style>

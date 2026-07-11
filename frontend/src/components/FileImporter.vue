<!--
  FileImporter.vue — CSV/XLSX 数据导入按钮
  Props:
    hint: 提示行 (可选, 描述期望列)
    template: 模板下载数据 (可选, 数组), 传了会显示"下载模板"按钮
  Emit:
    parsed({ rows, headers }): 解析成功
-->
<template>
  <div class="fi">
    <input ref="input" type="file" accept=".csv,.xlsx,.xls"
           style="display:none" @change="onFile">
    <el-button size="small" @click="input.click()">
      <el-icon><Upload /></el-icon>&nbsp;导入 CSV/Excel
    </el-button>
    <el-button v-if="template" size="small" link @click="dlTemplate">
      <el-icon><Download /></el-icon>&nbsp;下载模板
    </el-button>
    <span v-if="hint" class="hint">{{ hint }}</span>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Download } from '@element-plus/icons-vue'
import { parseFile } from '../composables/parseFile'
import * as XLSX from 'xlsx'

const props = defineProps({
  hint:     { type: String, default: '' },
  template: { type: Array,  default: null },  // eg [['指标','A','B'], ['质量',9,7], ...]
  templateName: { type: String, default: '模板' },
})
const emit = defineEmits(['parsed'])
const input = ref(null)

async function onFile (e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const parsed = await parseFile(file)
    if (!parsed.rows.length) {
      ElMessage.warning('文件为空'); return
    }
    emit('parsed', parsed)
    ElMessage.success(`已导入 ${parsed.rows.length - 1} 行数据`)
  } catch (err) {
    ElMessage.error(`解析失败: ${err.message || err}`)
  }
  e.target.value = ''  // 允许重复选同一文件
}

function dlTemplate () {
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet(props.template)
  XLSX.utils.book_append_sheet(wb, ws, 'Sheet1')
  XLSX.writeFile(wb, `qckit_${props.templateName}_模板.xlsx`)
}
</script>

<style scoped>
.fi { display: inline-flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.hint { color: #94a3b8; font-size: 11px; }
</style>

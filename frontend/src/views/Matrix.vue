<template>
  <ToolPage
    tool-key="matrix" title="矩阵图（Matrix Diagram / QFD）" icon-name="Grid"
    subtitle="两组因素的关系强度矩阵 · ● 强 ◎ 中 △ 弱 · AI 自动填格"
    :form="form" :analyze-fn="doAnalyze"
    :build-payload="(f, r) => r"
    :pptx-filename="f => `矩阵图_${f.topic || 'matrix'}.pptx`">
    <template #inputs>
      <el-form label-position="top" size="default">
        <el-form-item label="矩阵主题">
          <el-input v-model="form.topic" placeholder="如：QFD 客户需求 × 工程特性" />
        </el-form-item>
        <el-row :gutter="8">
          <el-col :span="12">
            <el-form-item label="行组标签">
              <el-input v-model="form.row_label" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="列组标签">
              <el-input v-model="form.col_label" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="行元素（每行一条）">
          <el-input v-model="form.rows_text" type="textarea" :rows="4"
                    placeholder="外观美观&#10;操作简单&#10;坚固耐用" />
        </el-form-item>
        <el-form-item label="列元素（每行一条）">
          <el-input v-model="form.cols_text" type="textarea" :rows="4"
                    placeholder="表面工艺&#10;按钮布局&#10;材料强度" />
        </el-form-item>
        <el-form-item label="背景（可选）">
          <el-input v-model="form.context" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </template>

    <template #results="{ result }">
      <div v-if="result.summary" class="result-section">
        <h4>💡 整体解读</h4>{{ result.summary }}
      </div>
      <div class="result-section">
        <h4>🔷 矩阵</h4>
        <div style="overflow:auto;">
          <table class="matrix-tbl">
            <thead>
              <tr>
                <th></th>
                <th>权</th>
                <th v-for="c in result.cols" :key="c">{{ c }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in result.rows" :key="r">
                <th>{{ r }}</th>
                <td class="w-cell">{{ result.row_weights?.[r] || '-' }}</td>
                <td v-for="c in result.cols" :key="c"
                    :class="'cell s-' + cellStrength(result, r, c)"
                    :title="cellReason(result, r, c)">
                  {{ cellSymbol(result, r, c) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-if="result.hot_spots?.length" class="result-section">
        <h4>🔥 Top 关键交叉点</h4>
        <ul style="margin:0;padding-left:18px;">
          <li v-for="(h,i) in result.hot_spots" :key="i">
            <b>{{ h.row }}</b> × <b>{{ h.col }}</b> → {{ h.action }}
          </li>
        </ul>
      </div>
      <div v-if="result.recommendations?.length" class="result-section">
        <h4>🎯 行动建议</h4>
        <ol style="margin:0;padding-left:18px;">
          <li v-for="(r,i) in result.recommendations" :key="i">{{ r }}</li>
        </ol>
      </div>
    </template>
  </ToolPage>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import ToolPage from '../components/ToolPage.vue'
import { analyzeMatrix } from '../api'

const form = reactive({
  topic: '', row_label: '需求', col_label: '特性',
  rows_text: '', cols_text: '', context: '',
})

async function doAnalyze (f) {
  if (!f.topic?.trim()) {
    ElMessage.warning('请填写矩阵主题'); throw new Error('invalid')
  }
  const rows = f.rows_text.split('\n').map(s => s.trim()).filter(Boolean)
  const cols = f.cols_text.split('\n').map(s => s.trim()).filter(Boolean)
  if (rows.length < 2 || cols.length < 2) {
    ElMessage.warning('行/列各至少填 2 条'); throw new Error('invalid')
  }
  if (new Set(rows).size !== rows.length || new Set(cols).size !== cols.length) {
    ElMessage.warning('行/列有重复条目'); throw new Error('invalid')
  }
  return await analyzeMatrix({
    topic: f.topic, row_label: f.row_label, col_label: f.col_label,
    rows, cols, context: f.context || null,
  })
}

function findCell (r, row, col) {
  return (r.cells || []).find(c => c.row === row && c.col === col)
}
function cellStrength (r, row, col) { return findCell(r, row, col)?.strength || 0 }
function cellSymbol (r, row, col) { return findCell(r, row, col)?.symbol || '' }
function cellReason (r, row, col) { return findCell(r, row, col)?.reason || '' }
</script>

<style scoped>
.matrix-tbl { border-collapse: collapse; font-size: 12px; }
.matrix-tbl th, .matrix-tbl td {
  border: 1px solid #e2e8f0; padding: 4px 8px; text-align: center;
  min-width: 40px;
}
.matrix-tbl thead th { background: #f1f5f9; }
.matrix-tbl tbody th { background: #f8fafc; text-align: right; }
.w-cell { color: #6366f1; font-weight: 600; }
.cell { font-weight: bold; font-size: 14px; }
.cell.s-9 { background: #fee2e2; color: #b91c1c; }
.cell.s-3 { background: #fef3c7; color: #92400e; }
.cell.s-1 { background: #f1f5f9; color: #64748b; }
</style>

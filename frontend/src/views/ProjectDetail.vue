<template>
  <div class="pd" v-if="p">
    <!-- 顶部 -->
    <div class="pd-hd">
      <el-button link @click="$router.push('/projects')">
        <el-icon><Back /></el-icon>&nbsp;返回项目列表
      </el-button>
      <div style="flex:1;"></div>
      <el-button @click="editing = true"><el-icon><Edit /></el-icon>&nbsp;编辑</el-button>
      <el-button type="primary" @click="doExport">
        <el-icon><Download /></el-icon>&nbsp;合成完整报告 PPTX
      </el-button>
    </div>

    <div class="proj-card">
      <h2 style="margin:0 0 6px;">{{ p.name }}</h2>
      <div class="meta">
        <span v-if="p.circle">🎯 {{ p.circle }}</span>
        <span v-if="p.leader">👤 {{ p.leader }}</span>
        <span v-if="p.members?.length">👥 {{ p.members.join('、') }}</span>
      </div>
      <div class="topic">{{ p.topic || '(未填主题)' }}</div>
    </div>

    <!-- 阶段 -->
    <div v-for="s in stagesList" :key="s.key" class="stage">
      <div class="stage-hd">
        <span class="stage-idx">{{ stageIndex(s.key) }}</span>
        <b>{{ s.label }}</b>
        <span class="cnt">{{ atts(s.key).length }} 份产出</span>
        <div style="flex:1;"></div>
        <el-tooltip content="从常用工具中选一个开始">
          <el-dropdown @command="goTool">
            <el-button size="small" type="primary" link>
              + 添加工具 <el-icon><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-for="t in TOOLS[s.key] || []" :key="t.key"
                                  :command="{tool:t.key,stage:s.key}">
                  {{ t.name }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-tooltip>
      </div>
      <div v-if="!atts(s.key).length" class="empty">
        （暂无产出 · 去工具页分析完后点「挂到项目」）
      </div>
      <div v-for="a in atts(s.key)" :key="a.id" class="att">
        <span class="att-tool">{{ TOOL_NAME[a.tool] || a.tool }}</span>
        <span class="att-title">{{ a.title }}</span>
        <span class="att-time">{{ (a.at || '').slice(5,16).replace('T',' ') }}</span>
        <el-button size="small" text @click="detach(s.key, a.id)">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editing" title="编辑项目" width="520">
      <el-form :model="edit" label-width="82">
        <el-form-item label="项目名"><el-input v-model="edit.name" /></el-form-item>
        <el-form-item label="项目主题"><el-input v-model="edit.topic" /></el-form-item>
        <el-form-item label="圈名"><el-input v-model="edit.circle" /></el-form-item>
        <el-form-item label="圈长"><el-input v-model="edit.leader" /></el-form-item>
        <el-form-item label="成员">
          <el-input v-model="edit.membersText" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editing = false">取消</el-button>
        <el-button type="primary" @click="doSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
  <el-empty v-else description="项目不存在或已删除" />
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Edit, Download, ArrowDown, Close } from '@element-plus/icons-vue'
import { getProject, updateProject, detachFromProject,
         downloadProjectPptx, projectsMeta } from '../api'

const route = useRoute(), router = useRouter()
const p = ref(null)
const meta = ref({ stages: [], stage_labels: {} })
const editing = ref(false)
const edit = reactive({ name:'', topic:'', circle:'', leader:'', membersText:'' })

// 每阶段的推荐工具
const TOOLS = {
  select:   [{key:'qcc_guide',name:'QCC 思路生成'}],
  current:  [{key:'relations',name:'关联图'},{key:'affinity',name:'亲和图'},{key:'pareto',name:'柏拉图'}],
  target:   [{key:'radar',name:'雷达图'}],
  cause:    [{key:'fishbone',name:'鱼骨图'},{key:'affinity',name:'亲和图'}],
  root:     [{key:'rca',name:'根因确认(5Why)'}],
  measure:  [{key:'tree',name:'系统图'},{key:'matrix',name:'矩阵图'},{key:'mda',name:'矩阵数据解析'},{key:'w5h2',name:'5W2H'}],
  schedule: [{key:'arrow',name:'箭线图'},{key:'pdpc',name:'PDPC'}],
  execute:  [{key:'pdpc',name:'PDPC 复盘'}],
  evaluate: [{key:'radar',name:'雷达图'},{key:'pareto',name:'柏拉图对比'}],
  standard: [{key:'tree',name:'系统图 (标准化)'},{key:'w5h2',name:'5W2H'}],
}
const TOOL_NAME = {
  qcc_guide:'QCC 思路', relations:'关联图', affinity:'亲和图', pareto:'柏拉图',
  radar:'雷达图', fishbone:'鱼骨图', rca:'根因确认', tree:'系统图',
  matrix:'矩阵图', mda:'矩阵数据解析', w5h2:'5W2H', arrow:'箭线图', pdpc:'PDPC',
}
const PATH = { qcc_guide: '/tools/qcc-guide' }

const stagesList = computed(() => meta.value.stages.map(k => ({
  key: k, label: meta.value.stage_labels[k],
})))
function stageIndex (key) {
  const i = meta.value.stages.indexOf(key)
  return ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩'][i] || ''
}
function atts (k) { return p.value?.stages?.[k] || [] }

async function load () {
  meta.value = await projectsMeta()
  try { p.value = await getProject(route.params.id) }
  catch { p.value = null }
}
onMounted(load)

function goTool ({ tool, stage }) {
  // 携带 project 上下文, ToolPage 会读并在分析后提示"挂到项目"
  sessionStorage.setItem('qckit.attach_target', JSON.stringify({
    project_id: p.value.id, project_name: p.value.name, stage,
  }))
  const path = PATH[tool] || `/tools/${tool}`
  router.push({ path, query: { topic: p.value.topic || '' } })
}

async function detach (stage, aid) {
  await detachFromProject(p.value.id, stage, aid)
  ElMessage.success('已移除')
  await load()
}
async function doExport () {
  await downloadProjectPptx(p.value.id, `QCC项目_${p.value.name}.pptx`)
}

// 编辑
function openEdit () {
  Object.assign(edit, {
    name: p.value.name, topic: p.value.topic,
    circle: p.value.circle, leader: p.value.leader,
    membersText: (p.value.members || []).join('、'),
  })
  editing.value = true
}
async function doSave () {
  const members = edit.membersText.split(/[,，、\n]/).map(s => s.trim()).filter(Boolean)
  await updateProject(p.value.id, {
    name: edit.name, topic: edit.topic,
    circle: edit.circle, leader: edit.leader, members,
  })
  editing.value = false
  ElMessage.success('已保存')
  await load()
}
// 打开编辑对话框时预填
import { watch } from 'vue'
watch(editing, v => { if (v) openEdit() })
</script>

<style scoped>
.pd { padding: 8px 4px; }
.pd-hd { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.proj-card {
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
  border: 1px solid #bfdbfe; border-radius: 8px;
  padding: 16px 20px; margin-bottom: 20px;
}
.meta { display: flex; gap: 14px; color: #64748b; font-size: 13px; margin-bottom: 6px; }
.topic { color: #1e293b; }

.stage {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 12px 16px; margin-bottom: 10px;
}
.stage-hd { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.stage-idx {
  display: inline-flex; width: 24px; height: 24px; align-items: center;
  justify-content: center; background: #1e40af; color: #fff; border-radius: 4px;
  font-size: 12px;
}
.stage-hd .cnt { color: #94a3b8; font-size: 12px; margin-left: 4px; }
.empty { color: #94a3b8; font-size: 12px; padding: 6px 0; }

.att {
  display: flex; align-items: center; gap: 10px; padding: 8px 10px;
  background: #f8fafc; border-radius: 4px; margin-bottom: 4px;
}
.att-tool {
  padding: 1px 6px; background: #dbeafe; color: #1e40af;
  border-radius: 3px; font-size: 11px; flex-shrink: 0;
}
.att-title { flex: 1; color: #1e293b; font-size: 13px; }
.att-time { color: #94a3b8; font-size: 11px; }
</style>

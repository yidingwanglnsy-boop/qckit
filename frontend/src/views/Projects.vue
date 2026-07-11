<template>
  <div class="proj-page">
    <div class="page-hd">
      <div>
        <h2 style="margin:0;">🎯 QCC 项目</h2>
        <div class="sub">一个项目串起选题→现状→要因→对策→执行→评估的全周期产物 · 一键合成完整报告</div>
      </div>
      <el-button type="primary" @click="showCreate = true">
        <el-icon><Plus /></el-icon>&nbsp;新建项目
      </el-button>
    </div>

    <el-empty v-if="!list.length" description="还没有项目 · 点右上「新建项目」开始">
      <el-button type="primary" @click="showCreate = true">新建第一个项目</el-button>
    </el-empty>

    <div v-for="p in list" :key="p.id" class="proj-card" @click="open(p)">
      <div class="proj-main">
        <div class="proj-title">
          <b>{{ p.name }}</b>
          <span class="proj-circle" v-if="p.circle">· {{ p.circle }}</span>
        </div>
        <div class="proj-topic">{{ p.topic || '(未填主题)' }}</div>
        <div class="proj-stats">
          <span v-for="s in stagesSummary(p)" :key="s.key" class="stat-chip"
                :class="{ done: s.count > 0 }">
            {{ s.label }} <b v-if="s.count > 0">{{ s.count }}</b>
          </span>
        </div>
      </div>
      <div class="proj-actions" @click.stop>
        <el-button size="small" @click="exportOne(p)">
          <el-icon><Download /></el-icon>&nbsp;合成 PPTX
        </el-button>
        <el-button size="small" @click="open(p)">打开</el-button>
        <el-button size="small" type="danger" text @click="dropOne(p)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 新建对话框 -->
    <el-dialog v-model="showCreate" title="新建 QCC 项目" width="520">
      <el-form :model="draft" label-width="82">
        <el-form-item label="项目名"><el-input v-model="draft.name" placeholder="如: 降低焊接不良率" /></el-form-item>
        <el-form-item label="项目主题"><el-input v-model="draft.topic" placeholder="如: 焊接不良率从 8% 降到 3%" /></el-form-item>
        <el-form-item label="圈名"><el-input v-model="draft.circle" placeholder="如: 精焊圈" /></el-form-item>
        <el-form-item label="圈长"><el-input v-model="draft.leader" placeholder="张工" /></el-form-item>
        <el-form-item label="成员">
          <el-input v-model="draft.membersText"
                    placeholder="用逗号或换行分隔" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="doCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Delete } from '@element-plus/icons-vue'
import { listProjects, createProject, deleteProject,
         downloadProjectPptx, projectsMeta } from '../api'

const list = ref([])
const meta = ref({ stages: [], stage_labels: {} })
const showCreate = ref(false)
const draft = reactive({ name:'', topic:'', circle:'', leader:'', membersText:'' })
const router = useRouter()

async function load () {
  list.value = await listProjects()
  meta.value = await projectsMeta()
}
onMounted(load)

function stagesSummary (p) {
  return meta.value.stages.map(k => ({
    key: k, label: meta.value.stage_labels[k],
    count: (p.stages?.[k] || []).length,
  }))
}
function open (p) { router.push(`/projects/${p.id}`) }
async function exportOne (p) {
  await downloadProjectPptx(p.id, `QCC项目_${p.name}.pptx`)
}
async function dropOne (p) {
  try {
    await ElMessageBox.confirm(`删除项目「${p.name}」？此操作不可恢复`, '确认', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消',
    })
    await deleteProject(p.id)
    ElMessage.success('已删除')
    await load()
  } catch {}
}
async function doCreate () {
  if (!draft.name.trim()) return ElMessage.warning('请填项目名')
  const members = draft.membersText.split(/[,，\n]/).map(s => s.trim()).filter(Boolean)
  const p = await createProject({
    name: draft.name, topic: draft.topic,
    circle: draft.circle, leader: draft.leader, members,
  })
  showCreate.value = false
  Object.assign(draft, { name:'', topic:'', circle:'', leader:'', membersText:'' })
  ElMessage.success('已创建')
  router.push(`/projects/${p.id}`)
}
</script>

<style scoped>
.proj-page { padding: 8px 4px; }
.page-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.sub { font-size: 12px; color: #64748b; margin-top: 4px; }

.proj-card {
  display: flex; gap: 16px; padding: 14px 18px; background: #fff;
  border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 10px;
  cursor: pointer; transition: all .15s;
}
.proj-card:hover { border-color: #60a5fa; box-shadow: 0 2px 8px rgba(59,130,246,.1); }
.proj-main { flex: 1; min-width: 0; }
.proj-title { font-size: 15px; margin-bottom: 4px; }
.proj-circle { color: #94a3b8; font-weight: 400; margin-left: 4px; font-size: 13px; }
.proj-topic { color: #64748b; font-size: 13px; margin-bottom: 8px; }
.proj-stats { display: flex; flex-wrap: wrap; gap: 4px; }
.stat-chip {
  padding: 2px 8px; font-size: 11px; border-radius: 3px;
  background: #f1f5f9; color: #94a3b8; border: 1px solid transparent;
}
.stat-chip.done { background: #dbeafe; color: #1e40af; border-color: #93c5fd; }
.stat-chip b { margin-left: 2px; }

.proj-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
</style>

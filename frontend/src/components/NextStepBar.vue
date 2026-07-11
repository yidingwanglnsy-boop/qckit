<!--
  NextStepBar.vue — QCC 工具间跳转推荐组件
  用法: <NextStepBar :from="'fishbone'" :topic="form.topic" />
  按 QCC 阶段顺序推荐下一步工具, 携带 topic query 直接跳转。
-->
<template>
  <div v-if="candidates.length" class="next-step">
    <div class="hd">
      <el-icon><Right /></el-icon> QCC 下一步
      <span class="tip">带上当前主题跳转，避免重复输入</span>
    </div>
    <div class="btns">
      <el-button v-for="c in candidates" :key="c.key" size="default"
                 :type="c.emphasis ? 'primary' : ''"
                 @click="goto(c)">
        <span class="stage">{{ c.stage }}</span>
        <span class="name">{{ c.name }}</span>
        <el-icon style="margin-left:4px;"><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Right, ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  from: { type: String, required: true },   // 当前工具 key
  topic: { type: String, default: '' },
})
const router = useRouter()

// QCC 全周期典型链路: 选题→现状/要因→根因→对策→排期→执行→评估
// 每条从 X 出发时, 推荐下 2-3 个最常见的后续工具
const NEXT = {
  qcc_guide: [
    { key:'relations', name:'关联图', stage:'现状调查', emphasis:true },
    { key:'affinity',  name:'亲和图', stage:'现状调查' },
    { key:'pareto',    name:'柏拉图', stage:'现状调查' },
  ],
  relations: [
    { key:'fishbone', name:'鱼骨图', stage:'要因分析', emphasis:true },
    { key:'affinity', name:'亲和图', stage:'要因分类' },
    { key:'tree',     name:'系统图', stage:'目标拆解' },
  ],
  affinity: [
    { key:'fishbone', name:'鱼骨图', stage:'要因分析', emphasis:true },
    { key:'relations',name:'关联图', stage:'因果分析' },
  ],
  pareto: [
    { key:'fishbone', name:'鱼骨图', stage:'要因分析', emphasis:true },
    { key:'w5h2',     name:'5W2H',   stage:'对策制定' },
    { key:'rca',      name:'根因确认', stage:'根因确认' },
  ],
  fishbone: [
    { key:'rca',    name:'根因确认', stage:'根因确认', emphasis:true },
    { key:'w5h2',   name:'5W2H',    stage:'对策制定' },
    { key:'matrix', name:'矩阵图',  stage:'对策优选' },
  ],
  rca: [
    { key:'w5h2',   name:'5W2H',   stage:'对策制定', emphasis:true },
    { key:'tree',   name:'系统图', stage:'对策拆解' },
    { key:'pdpc',   name:'PDPC',   stage:'预案规划' },
  ],
  tree: [
    { key:'matrix', name:'矩阵图', stage:'对策优选', emphasis:true },
    { key:'arrow',  name:'箭线图', stage:'任务排期' },
    { key:'pdpc',   name:'PDPC',   stage:'风险预案' },
  ],
  matrix: [
    { key:'arrow', name:'箭线图', stage:'任务排期', emphasis:true },
    { key:'pdpc',  name:'PDPC',   stage:'风险预案' },
    { key:'radar', name:'雷达图', stage:'效果评估' },
  ],
  mda: [
    { key:'matrix', name:'矩阵图', stage:'关系分析' },
    { key:'radar',  name:'雷达图', stage:'对比展示' },
  ],
  w5h2: [
    { key:'arrow', name:'箭线图', stage:'任务排期', emphasis:true },
    { key:'pdpc',  name:'PDPC',   stage:'风险预案' },
  ],
  pdpc: [
    { key:'arrow', name:'箭线图', stage:'任务排期', emphasis:true },
    { key:'radar', name:'雷达图', stage:'效果评估' },
  ],
  arrow: [
    { key:'radar', name:'雷达图', stage:'效果评估', emphasis:true },
    { key:'pareto',name:'柏拉图', stage:'效果对比' },
  ],
  radar: [
    { key:'pareto', name:'柏拉图', stage:'剩余症结' },
    { key:'w5h2',   name:'5W2H',   stage:'标准化' },
  ],
}
// key 到路由的映射 (qcc_guide 特殊路径)
const PATH = {
  qcc_guide: '/tools/qcc-guide',
}
function pathOf (key) { return PATH[key] || `/tools/${key}` }

const candidates = computed(() => NEXT[props.from] || [])

function goto (c) {
  router.push({
    path: pathOf(c.key),
    query: props.topic ? { topic: props.topic } : {},
  })
}
</script>

<style scoped>
.next-step {
  margin: 14px 0; padding: 12px 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
  border: 1px solid #bfdbfe; border-radius: 8px;
}
.hd {
  display: flex; align-items: center; gap: 6px;
  font-weight: 600; color: #1e40af; margin-bottom: 8px;
}
.tip {
  font-weight: 400; font-size: 11px; color: #64748b;
  margin-left: auto;
}
.btns { display: flex; flex-wrap: wrap; gap: 8px; }
.btns .el-button {
  display: inline-flex; align-items: center; height: auto;
  padding: 6px 12px; text-align: left;
}
.stage {
  font-size: 10px; color: #64748b; margin-right: 6px;
  padding: 1px 6px; background: #fff; border-radius: 3px;
  border: 1px solid #cbd5e1;
}
.el-button--primary .stage { color: #1e40af; background: #dbeafe; border-color: #93c5fd; }
.name { font-size: 13px; }
</style>

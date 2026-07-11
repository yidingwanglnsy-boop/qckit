<template>
  <el-container style="height: 100%;">
    <el-aside :width="collapsed ? '64px' : '220px'"
              style="background:#0f172a;color:#cbd5e1;transition:width .2s;position:relative;">
      <div class="brand-bar" :class="{ collapsed }">
        <span v-if="!collapsed">🛠 QCKit</span>
        <span v-else>🛠</span>
      </div>
      <el-menu :default-active="$route.path" router :collapse="collapsed"
        :collapse-transition="false"
        background-color="#0f172a" text-color="#cbd5e1" active-text-color="#60a5fa">
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon><template #title>首页</template>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Files /></el-icon><template #title>我的项目</template>
        </el-menu-item>
        <el-menu-item index="/tools/qcc-guide">
          <el-icon><Guide /></el-icon><template #title>QCC 思路生成器</template>
        </el-menu-item>
        <el-sub-menu index="new-qc">
          <template #title>
            <el-icon><Grid /></el-icon><span>新QC七大手法</span>
          </template>
          <el-menu-item index="/tools/relations">
            <el-icon><Share /></el-icon><template #title>关联图</template>
          </el-menu-item>
          <el-menu-item index="/tools/affinity">
            <el-icon><Collection /></el-icon><template #title>亲和图（KJ）</template>
          </el-menu-item>
          <el-menu-item index="/tools/tree">
            <el-icon><Grid /></el-icon><template #title>系统图</template>
          </el-menu-item>
          <el-menu-item index="/tools/matrix">
            <el-icon><Grid /></el-icon><template #title>矩阵图（QFD）</template>
          </el-menu-item>
          <el-menu-item index="/tools/mda">
            <el-icon><DataAnalysis /></el-icon><template #title>矩阵数据解析</template>
          </el-menu-item>
          <el-menu-item index="/tools/pdpc">
            <el-icon><Compass /></el-icon><template #title>PDPC 决策程序图</template>
          </el-menu-item>
          <el-menu-item index="/tools/arrow">
            <el-icon><Right /></el-icon><template #title>箭线图（CPM）</template>
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="old-qc">
          <template #title>
            <el-icon><DataAnalysis /></el-icon><span>QC七大手法</span>
          </template>
          <el-menu-item index="/tools/pareto">
            <el-icon><TrendCharts /></el-icon><template #title>柏拉图</template>
          </el-menu-item>
          <el-menu-item index="/tools/fishbone">
            <el-icon><Share /></el-icon><template #title>鱼骨图（4M）</template>
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="general">
          <template #title>
            <el-icon><Aim /></el-icon><span>通用工具</span>
          </template>
          <el-menu-item index="/tools/radar">
            <el-icon><Aim /></el-icon><template #title>雷达图</template>
          </el-menu-item>
          <el-menu-item index="/tools/w5h2">
            <el-icon><Grid /></el-icon><template #title>5W2H 分析</template>
          </el-menu-item>
          <el-menu-item index="/tools/rca">
            <el-icon><Search /></el-icon><template #title>根因确认</template>
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="config">
          <template #title>
            <el-icon><Setting /></el-icon><span>配置</span>
          </template>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon><template #title>历史记录</template>
          </el-menu-item>
          <el-menu-item index="/brand">
            <el-icon><Brush /></el-icon><template #title>品牌主题</template>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Tools /></el-icon><template #title>大模型 API</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>

      <div class="collapse-btn" @click="collapsed = !collapsed" :title="collapsed ? '展开' : '收起'">
        <el-icon><ArrowRight v-if="collapsed" /><ArrowLeft v-else /></el-icon>
      </div>
      <div v-if="!collapsed" class="footer-tag">v0.2.0 · PolyForm NC</div>
    </el-aside>

    <el-main style="padding: 20px;">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
const collapsed = ref(false)

const KEY = 'qckit.sidebar.collapsed'
onMounted(() => {
  collapsed.value = localStorage.getItem(KEY) === '1'
  window.addEventListener('keydown', guardBackspace, true)
})
onBeforeUnmount(() => window.removeEventListener('keydown', guardBackspace, true))
watch(collapsed, v => localStorage.setItem(KEY, v ? '1' : '0'))

/** 阻止焦点不在输入元素上时 Backspace 触发浏览器历史后退。 */
function guardBackspace(e) {
  if (e.key !== 'Backspace') return
  const t = e.target
  const tag = (t?.tagName || '').toUpperCase()
  const editable = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'
                || t?.isContentEditable
  if (!editable) e.preventDefault()
}
</script>

<style scoped>
.brand-bar {
  padding: 18px; font-size: 20px; font-weight: 600; color: #fff;
  letter-spacing: 1px; text-align: left; height: 24px; line-height: 24px;
}
.brand-bar.collapsed { text-align: center; padding: 18px 0; }
.collapse-btn {
  position: absolute; bottom: 44px; left: 50%; transform: translateX(-50%);
  width: 28px; height: 28px; border-radius: 14px;
  background: #1e293b; color: #94a3b8; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; transition: background .15s, color .15s;
}
.collapse-btn:hover { background: #334155; color: #60a5fa; }
.footer-tag {
  position: absolute; bottom: 12px; left: 18px;
  font-size: 12px; color: #64748b;
}
</style>

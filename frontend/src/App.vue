<template>
  <el-container style="height: 100%;">
    <el-aside width="220px" style="background:#0f172a;color:#cbd5e1;">
      <div style="padding:20px 18px;font-size:20px;font-weight:600;color:#fff;letter-spacing:1px;">
        🛠 QCKit
      </div>
      <el-menu :default-active="$route.path" router
        background-color="#0f172a" text-color="#cbd5e1" active-text-color="#60a5fa">
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon><span>首页</span>
        </el-menu-item>
        <el-sub-menu index="new-qc">
          <template #title>
            <el-icon><Grid /></el-icon><span>新QC七大手法</span>
          </template>
          <el-menu-item index="/tools/relations">
            <el-icon><Share /></el-icon>关联图
          </el-menu-item>
          <el-menu-item index="/tools/affinity">
            <el-icon><Collection /></el-icon>亲和图（KJ）
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="old-qc">
          <template #title>
            <el-icon><DataAnalysis /></el-icon><span>QC七大手法</span>
          </template>
          <el-menu-item index="/tools/pareto">
            <el-icon><TrendCharts /></el-icon>柏拉图
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon><span>LLM 配置</span>
        </el-menu-item>
      </el-menu>
      <div style="position:absolute;bottom:12px;left:18px;font-size:12px;color:#64748b;">
        v0.2.0 · MIT
      </div>
    </el-aside>
    <el-main style="padding: 24px;">
      <router-view />
    </el-main>
  </el-container>
</template>

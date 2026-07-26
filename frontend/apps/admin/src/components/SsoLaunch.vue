<template>
  <div class="page-card sso">
    <h2 class="page-title">{{ title }}</h2>
    <p class="desc">该功能在现网为独立 SSO 子系统，本地提供跳转入口（不伪造第三方后台）。</p>
    <el-descriptions :column="1" border>
      <el-descriptions-item label="系统">{{ title }}</el-descriptions-item>
      <el-descriptions-item label="目标地址">{{ url }}</el-descriptions-item>
    </el-descriptions>
    <div style="margin-top:16px">
      <el-button type="primary" @click="open">打开外链系统</el-button>
      <el-button @click="$router.back()">返回</el-button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  title: { type: String, default: '外部系统' },
  url: { type: String, required: true },
})
function open() {
  window.open(props.url, '_blank')
}
</script>

<style scoped>
.desc { color:#678; margin: 8px 0 16px; }
</style>

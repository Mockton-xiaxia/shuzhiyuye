<template>
  <el-container class="layout">
    <el-aside width="232px" class="aside">
      <div class="brand">
        <div class="logo">渔</div>
        <div>
          <div class="name">数智渔业</div>
          <div class="sub">{{ portalLabel }}</div>
        </div>
      </div>
      <el-menu :default-active="active" router background-color="transparent" text-color="#d7efe7" active-text-color="#fff">
        <template v-for="m in auth.menus" :key="m.id">
          <el-sub-menu v-if="m.children?.length" :index="m.path || String(m.id)">
            <template #title>{{ m.name }}</template>
            <el-menu-item v-for="c in m.children" :key="c.id" :index="normalize(c.path)">{{ c.name }}</el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="normalize(m.path)">{{ m.name }}</el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="left">绿色循环渔业试点</div>
        <div class="right">
          <el-tag size="small" type="success">{{ auth.user?.realName || auth.user?.username }}</el-tag>
          <el-button link type="primary" @click="goTrace">公开追溯样例</el-button>
          <el-button link @click="onLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const active = computed(() => route.path)
const portalLabel = computed(() => (auth.portal === 'ENT' ? '企业工作台' : '区县监管端'))

function normalize(path) {
  if (!path) return '/'
  return path.startsWith('/') ? path : `/${path}`
}
function onLogout() {
  auth.logout()
  router.push('/login')
}
function goTrace() {
  window.open('/p/trace/NZTRACE20260001', '_blank')
}
</script>

<style scoped>
.layout { height: 100%; }
.aside {
  background: linear-gradient(180deg, #0b6e4f 0%, #0a4f4f 100%);
  color: #fff;
  overflow: auto;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 18px 16px;
}
.logo {
  width: 36px; height: 36px; border-radius: 10px;
  background: rgba(255,255,255,.18);
  display: grid; place-items: center; font-weight: 700;
}
.name { font-weight: 700; }
.sub { font-size: 12px; opacity: .8; }
.header {
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; border-bottom: 1px solid #e6eeea;
}
.right { display: flex; gap: 10px; align-items: center; }
.main { padding: 16px; }
:deep(.el-menu) { border-right: none; }
:deep(.el-menu-item.is-active) { background: rgba(255,255,255,.14) !important; }
</style>

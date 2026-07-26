<template>
  <div class="login">
    <div class="panel">
      <h1>数智渔业平台</h1>
      <p>绿色循环渔业 · 双门户登录</p>
      <el-form @submit.prevent="onSubmit">
        <el-form-item label="账号">
          <el-input v-model="form.username" placeholder="gov_admin / ent_admin" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">登录</el-button>
      </el-form>
      <div class="tips">演示：区县 gov_admin / 企业 ent_admin，密码 123456</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const form = reactive({ username: 'gov_admin', password: '123456' })

async function onSubmit() {
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push(auth.portal === 'ENT' ? '/ent/workbench' : '/gov/workbench')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100%;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 20% 20%, rgba(8,164,167,.25), transparent 40%),
    radial-gradient(circle at 80% 0%, rgba(11,110,79,.28), transparent 35%),
    linear-gradient(160deg, #e9f5f1, #f7faf8 55%, #dff0ea);
}
.panel {
  width: 420px;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 20px 50px rgba(10,60,40,.12);
}
h1 { margin: 0 0 6px; color: #0b6e4f; }
p { margin: 0 0 18px; color: #678; }
.tips { margin-top: 14px; font-size: 12px; color: #89a; }
</style>

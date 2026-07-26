<template>
  <div class="page-card">
    <h2 class="page-title">质量整改</h2>
    <el-table :data="list" stripe>
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="content" label="要求" min-width="180" />
      <el-table-column prop="reply" label="回复" min-width="140" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button v-if="isEnt && row.status==='PENDING'" link @click="accept(row)">接收</el-button>
          <el-button v-if="isEnt && ['PENDING','RECTIFYING'].includes(row.status)" link type="primary" @click="reply(row)">回复</el-button>
          <el-button v-if="isGov && row.status==='REVIEW'" link type="success" @click="review(row,true)">通过</el-button>
          <el-button v-if="isGov && row.status==='REVIEW'" link type="danger" @click="review(row,false)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
const auth = useAuthStore()
const isGov = computed(() => auth.portal === 'GOV')
const isEnt = computed(() => auth.portal === 'ENT')
const list = ref([])
async function load(){ list.value = (await http.get('/quality/rectifications')).data || [] }
async function accept(row){ await http.post(`/quality/rectifications/${row.id}/accept`); load() }
async function reply(row){
  const { value } = await ElMessageBox.prompt('整改说明', '回复整改')
  await http.post(`/quality/rectifications/${row.id}/reply`, { reply: value })
  ElMessage.success('已提交复查'); load()
}
async function review(row, approved){
  await http.post(`/quality/rectifications/${row.id}/review`, { approved, opinion: approved ? '通过' : '需继续整改' })
  load()
}
onMounted(load)
</script>

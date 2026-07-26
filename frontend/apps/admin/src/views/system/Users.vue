<template>
  <SimpleTablePage title="用户管理" :rows="list" :columns="cols" :actions="[{label:'新建用户', onClick: create}]" />
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import http from '@/api/http'
import SimpleTablePage from '@/components/SimpleTablePage.vue'
const list = ref([])
const cols = [
  { prop: 'username', label: '账号' },
  { prop: 'realName', label: '姓名' },
  { prop: 'userType', label: '类型', width: 120 },
  { prop: 'status', label: '状态', width: 80 },
  { prop: 'mobile', label: '手机', width: 130 },
]
async function load() { list.value = (await http.get('/system/users')).data || [] }
async function create() {
  const { value: username } = await ElMessageBox.prompt('用户名', '新建用户')
  await http.post('/system/users', { username, realName: username, userType: 'COUNTY', roleCode: 'COUNTY_ADMIN' })
  ElMessage.success('已创建'); load()
}
onMounted(load)
</script>

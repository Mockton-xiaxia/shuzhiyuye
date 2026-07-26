<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">产品入库 · 捕捞入库</h2>
      <div>
        <el-button type="primary" @click="dlg=true">捕捞入库</el-button>
        <el-button @click="load">刷新</el-button>
      </div>
    </div>
    <el-table :data="rows" stripe v-loading="loading">
      <el-table-column prop="itemName" label="品种/品名" />
      <el-table-column prop="qty" label="数量(kg)" width="110" />
      <el-table-column prop="source" label="来源" width="100">
        <template #default="{ row }">{{ row.source === 'CATCH' ? '捕捞入库' : row.source }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column prop="createdAt" label="入库日期" min-width="160" />
    </el-table>

    <el-dialog v-model="dlg" title="捕捞入库" width="480px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="品种"><el-input v-model="form.itemName" placeholder="商品大鲵" /></el-form-item>
        <el-form-item label="产品类型">
          <el-select v-model="form.productType" style="width:100%">
            <el-option label="鲜活" value="鲜活" />
            <el-option label="冰鲜" value="冰鲜" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源塘口"><el-input v-model="form.pondName" placeholder="1号养殖塘" /></el-form-item>
        <el-form-item label="数量(kg)"><el-input-number v-model="form.qty" :min="0.1" :step="1" /></el-form-item>
        <el-form-item label="保质期"><el-date-picker v-model="form.expireDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确认入库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const rows = ref([])
const loading = ref(false)
const dlg = ref(false)
const saving = ref(false)
const form = reactive({
  itemName: '商品大鲵',
  productType: '鲜活',
  pondName: '1号养殖塘',
  qty: 50,
  expireDate: '2026-08-22',
})

async function load() {
  loading.value = true
  try {
    const res = await http.get('/wms/inbounds', { params: { category: 'PRODUCT' } })
    rows.value = res.data || []
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await http.post('/wms/inbounds', {
      itemName: form.itemName,
      qty: form.qty,
      category: 'PRODUCT',
      source: 'CATCH',
    })
    ElMessage.success(`捕捞入库成功 · ${form.pondName} · ${form.productType}`)
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
</style>

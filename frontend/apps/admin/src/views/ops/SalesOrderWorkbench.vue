<template>
  <div class="page-card">
    <div class="bar">
      <h2 class="page-title">{{ title }}</h2>
      <div class="actions">
        <el-button @click="load">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button type="primary" @click="openCreate">新增订单</el-button>
      </div>
    </div>
    <el-tabs v-model="tab">
      <el-tab-pane label="销售订单" name="orders">
        <el-form inline class="filters">
          <el-form-item label="状态">
            <el-select v-model="q.status" clearable style="width:130px">
              <el-option label="草稿" value="DRAFT" />
              <el-option label="已确认" value="CONFIRMED" />
              <el-option label="已履约" value="DONE" />
              <el-option label="已取消" value="CANCELLED" />
            </el-select>
          </el-form-item>
          <el-form-item label="客户"><el-input v-model="q.buyer" clearable style="width:140px" /></el-form-item>
        </el-form>
        <el-table :data="filtered" stripe v-loading="loading">
          <el-table-column prop="orderNo" label="订单编号" min-width="130" />
          <el-table-column prop="buyer" label="客户名称" min-width="120" />
          <el-table-column prop="orderDate" label="下单日期" width="110" />
          <el-table-column prop="productName" label="产品名称" width="110" />
          <el-table-column prop="qty" label="销售数量" width="90" />
          <el-table-column prop="unitPrice" label="单价(元)" width="90" />
          <el-table-column prop="amount" label="总金额(元)" width="110" />
          <el-table-column prop="deliverDate" label="交付日期" width="110" />
          <el-table-column prop="status" label="订单状态" width="100">
            <template #default="{ row }"><el-tag size="small">{{ statusLabel(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status==='DRAFT' || row.status==='CREATED'" link type="warning" @click="confirm(row)">确认</el-button>
              <el-button v-if="row.status==='CONFIRMED'" link type="success" @click="fulfill(row)">履约</el-button>
              <el-button v-if="row.status==='DRAFT' || row.status==='CREATED' || row.status==='CONFIRMED'" link type="danger" @click="cancel(row)">取消</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="数据追溯" name="trace">
        <el-table :data="doneRows" stripe>
          <el-table-column prop="orderNo" label="订单编号" />
          <el-table-column prop="buyer" label="客户" />
          <el-table-column prop="productName" label="产品" />
          <el-table-column prop="traceHint" label="追溯说明" min-width="180" />
          <el-table-column prop="status" label="状态" width="90" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="dlg" title="新增销售订单" width="500px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="客户名称"><el-input v-model="form.buyer" placeholder="本地水产批发商" /></el-form-item>
        <el-form-item label="产品名称"><el-input v-model="form.productName" /></el-form-item>
        <el-form-item label="销售数量"><el-input-number v-model="form.qty" :min="0" :step="1" style="width:100%" /></el-form-item>
        <el-form-item label="单价(元)"><el-input-number v-model="form.unitPrice" :min="0" :step="1" style="width:100%" /></el-form-item>
        <el-form-item label="交付日期"><el-date-picker v-model="form.deliverDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dlg=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

defineProps({ title: { type: String, default: '销售管理' } })

const tab = ref('orders')
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const dlg = ref(false)
const q = reactive({ status: '', buyer: '' })
const form = reactive({
  buyer: '本地水产批发商',
  productName: '商品大鲵',
  qty: 50,
  unitPrice: 180,
  deliverDate: '2026-07-30',
})

function statusLabel(s) {
  return ({ DRAFT: '草稿', CREATED: '草稿', CONFIRMED: '已确认', DONE: '已履约', CANCELLED: '已取消' })[s] || s
}
const filtered = computed(() =>
  rows.value.filter((r) => {
    if (q.status && r.status !== q.status && !(q.status === 'DRAFT' && r.status === 'CREATED')) return false
    if (q.buyer && !String(r.buyer || '').includes(q.buyer)) return false
    return true
  }),
)
const doneRows = computed(() => rows.value.filter((r) => r.status === 'DONE'))

async function load() {
  loading.value = true
  try {
    const res = await http.get('/circulation/sales-orders')
    rows.value = res.data || []
  } finally {
    loading.value = false
  }
}
function reset() {
  q.status = ''
  q.buyer = ''
  load()
}
function openCreate() {
  dlg.value = true
}
async function save() {
  saving.value = true
  try {
    await http.post('/circulation/sales-orders', { ...form })
    ElMessage.success('订单已创建')
    dlg.value = false
    load()
  } finally {
    saving.value = false
  }
}
async function confirm(row) {
  await http.post(`/circulation/sales-orders/${row.id}/confirm`)
  ElMessage.success('订单已确认')
  load()
}
async function fulfill(row) {
  await http.post(`/circulation/sales-orders/${row.id}/fulfill`)
  ElMessage.success('已履约，并生成运输单')
  load()
}
async function cancel(row) {
  await http.post(`/circulation/sales-orders/${row.id}/cancel`)
  ElMessage.success('订单已取消')
  load()
}

onMounted(load)
</script>

<style scoped>
.bar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px; }
.actions { display:flex; gap:8px; }
.filters { margin-bottom:8px; }
</style>

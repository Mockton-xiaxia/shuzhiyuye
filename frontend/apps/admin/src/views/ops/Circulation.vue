<template>
  <div class="page-card">
    <h2 class="page-title">流通销售</h2>
    <el-tabs v-model="tab">
      <el-tab-pane label="销售订单" name="orders">
        <div style="margin-bottom:12px"><el-button type="primary" size="small" @click="createOrder">新建订单</el-button></div>
        <el-table :data="orders" stripe>
          <el-table-column prop="orderNo" label="单号" width="160" />
          <el-table-column prop="buyer" label="买方" />
          <el-table-column prop="amount" label="金额" width="100" />
          <el-table-column prop="status" label="状态" width="100" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="运输" name="transports">
        <div style="margin-bottom:12px"><el-button type="primary" size="small" @click="createTransport">登记运输</el-button></div>
        <el-table :data="transports" stripe>
          <el-table-column prop="plateNo" label="车牌" width="120" />
          <el-table-column prop="fromAddr" label="起点" />
          <el-table-column prop="toAddr" label="终点" />
          <el-table-column prop="status" label="状态" width="100" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { ElMessageBox } from 'element-plus'
import http from '@/api/http'
const tab = ref('orders')
const orders = ref([])
const transports = ref([])
async function load() {
  orders.value = (await http.get('/circulation/sales-orders')).data || []
  transports.value = (await http.get('/circulation/transports')).data || []
}
async function createOrder() {
  const { value } = await ElMessageBox.prompt('买方')
  await http.post('/circulation/sales-orders', { orderNo: 'SO' + Date.now(), buyer: value, amount: 1000 })
  load()
}
async function createTransport() {
  const { value } = await ElMessageBox.prompt('车牌')
  await http.post('/circulation/transports', { plateNo: value, fromAddr: '示范镇', toAddr: '示范市' })
  load()
}
onMounted(load)
</script>

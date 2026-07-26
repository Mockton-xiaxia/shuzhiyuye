<template>
  <Workbench v-if="feat?.shape === 'workbench'" />
  <SsoLaunch v-else-if="feat?.shape === 'sso'" :title="feat.name" :url="feat.ssoUrl" />
  <GisMapPage
    v-else-if="feat?.shape === 'gis'"
    :title="feat.name"
    :mode="gisMode"
  />
  <VideoMonitor
    v-else-if="isVideo"
    :scene="route.path.includes('wms/video') ? 'WAREHOUSE' : ''"
  />
  <EzvizConfig v-else-if="feat?.shape === 'ezviz' || route.path.includes('/iot/ezviz')" />
  <InspectionWorkbench
    v-else-if="isQualityInspect"
    :title="feat.name"
    :api="feat.api || '/quality/inspections'"
    :mode="qualityMode"
  />
  <RectificationWorkbench
    v-else-if="route.path.includes('/quality/rectifications')"
    :title="feat?.name || '质量整改'"
  />
  <TraceApplyWorkbench
    v-else-if="route.path.includes('/trace/applies') || route.path.includes('/quality/trace-apply')"
    :title="feat?.name || '标识申请'"
  />
  <DispatchWorkbench
    v-else-if="route.path.includes('/effluent/dispatches')"
    :title="feat?.name || '指挥调度记录'"
  />
  <EfRectWorkbench
    v-else-if="route.path.includes('/effluent/rectifications')"
    :title="feat?.name || '整改记录'"
  />
  <PlanWorkbench
    v-else-if="route.path.includes('/effluent/plans')"
    :title="feat?.name || '尾水排放计划'"
  />
  <AlarmWorkbench
    v-else-if="route.path.includes('/iot/alarms')"
    :title="feat?.name || '设备预警'"
  />
  <SalesOrderWorkbench
    v-else-if="route.path.includes('/circulation/sales') || route.path.includes('/circulation/match')"
    :title="feat?.name || '销售管理'"
  />
  <Portrait v-else-if="route.path.includes('/ledger/portrait')" />
  <AnalysisCharts v-else-if="route.path.includes('/ledger/analysis')" />
  <CatchInbound v-else-if="route.path.includes('/wms/product-in')" />
  <StocktakePage v-else-if="route.path.includes('/wms/stocktake')" />
  <EnterpriseWorkbench
    v-else-if="isEnterprisePage"
    :title="feat?.name || '养殖主体'"
    :mode="enterpriseMode"
  />
  <UavPatrolWorkbench
    v-else-if="feat?.shape === 'uav' || route.path.includes('/uav/patrol')"
    :title="feat?.name || '无人机巡查'"
  />
  <DomesticationWorkbench
    v-else-if="feat?.shape === 'domestication' || route.path.includes('/specialty/domestication')"
    :title="feat?.name || '育种驯化管理'"
  />
  <CrudPage
    v-else-if="feat?.shape === 'crud'"
    :key="route.path"
    ref="crud"
    :title="feat.name"
    :api="feat.api || '/feature/demo'"
    :columns="feat.columns || []"
    :buttons="feat.buttons || ['query', 'reset', 'create']"
    :filters="filters"
    :create-fields="createFields"
    :row-actions="rowActions"
    :create-label="createLabel"
    :readonly="!!feat?.readonly"
  />
  <div v-else class="page-card">未配置功能：{{ route.path }}</div>
</template>

<script setup>
import { computed, ref, defineAsyncComponent } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import catalog from '@/catalog/features.json'
import CrudPage from '@/components/CrudPage.vue'

const GisMapPage = defineAsyncComponent(() => import('@/components/GisMapPage.vue'))
const SsoLaunch = defineAsyncComponent(() => import('@/components/SsoLaunch.vue'))
const Workbench = defineAsyncComponent(() => import('@/views/Workbench.vue'))
const VideoMonitor = defineAsyncComponent(() => import('@/views/iot/VideoMonitor.vue'))
const EzvizConfig = defineAsyncComponent(() => import('@/views/iot/EzvizConfig.vue'))
const InspectionWorkbench = defineAsyncComponent(() => import('@/views/quality/InspectionWorkbench.vue'))
const RectificationWorkbench = defineAsyncComponent(() => import('@/views/quality/RectificationWorkbench.vue'))
const TraceApplyWorkbench = defineAsyncComponent(() => import('@/views/trace/TraceApplyWorkbench.vue'))
const DispatchWorkbench = defineAsyncComponent(() => import('@/views/effluent/DispatchWorkbench.vue'))
const EfRectWorkbench = defineAsyncComponent(() => import('@/views/effluent/EfRectWorkbench.vue'))
const PlanWorkbench = defineAsyncComponent(() => import('@/views/effluent/PlanWorkbench.vue'))
const AlarmWorkbench = defineAsyncComponent(() => import('@/views/iot/AlarmWorkbench.vue'))
const SalesOrderWorkbench = defineAsyncComponent(() => import('@/views/ops/SalesOrderWorkbench.vue'))
const Portrait = defineAsyncComponent(() => import('@/views/ops/Portrait.vue'))
const AnalysisCharts = defineAsyncComponent(() => import('@/views/ops/AnalysisCharts.vue'))
const CatchInbound = defineAsyncComponent(() => import('@/views/ops/CatchInbound.vue'))
const StocktakePage = defineAsyncComponent(() => import('@/views/ops/StocktakePage.vue'))
const EnterpriseWorkbench = defineAsyncComponent(() => import('@/views/party/EnterpriseWorkbench.vue'))
const UavPatrolWorkbench = defineAsyncComponent(() => import('@/views/uav/UavPatrolWorkbench.vue'))
const DomesticationWorkbench = defineAsyncComponent(() => import('@/views/specialty/DomesticationWorkbench.vue'))

const route = useRoute()
const auth = useAuthStore()
const crud = ref(null)

const all = [...(catalog.GOV || []), ...(catalog.ENT || [])]
const feat = computed(() => all.find((f) => f.path === route.path) || null)

const isVideo = computed(
  () =>
    (route.path.includes('/iot/cameras') ||
      route.path.includes('/iot/video') ||
      route.path.includes('/wms/video')) &&
    !route.path.includes('/iot/ezviz'),
)

const isEnterprisePage = computed(() => {
  const p = route.path
  return p.includes('/party/enterprises') || p.includes('/base/enterprise')
})

const enterpriseMode = computed(() => (route.path.includes('/base/enterprise') ? 'self' : 'gov'))

const isQualityInspect = computed(() => {
  const p = route.path
  return (
    p.includes('/quality/inspections') ||
    p.includes('/quality/self-checks') ||
    p.includes('/quality/gov-checks') ||
    p.includes('/quality/regulation') ||
    p.includes('/quality/control')
  )
})

const qualityMode = computed(() => {
  const p = route.path
  if (p.includes('self-checks')) return 'self'
  if (p.includes('gov-checks') || p.includes('regulation') || p.includes('control')) return 'readonly'
  return 'gov'
})

const createLabel = computed(() => {
  if (route.path.includes('/wms/') && route.path.includes('-in')) return '新增入库'
  return '新增'
})

const gisMode = computed(() => {
  const p = route.path
  if (p.includes('gis-audit') || p.includes('信息审核')) return 'audit'
  if (p.includes('gis-stats') || p.includes('统计')) return 'stats'
  return 'collect'
})

const filters = computed(() => {
  const cols = feat.value?.columns || []
  return cols.slice(0, 2).map((c) => ({ prop: c.prop, label: c.label, placeholder: c.label }))
})

const createFields = computed(() => {
  if (feat.value?.createFields?.length) return feat.value.createFields
  return (feat.value?.columns || []).map((c) => {
    const p = c.prop || ''
    let type = 'input'
    if (p.includes('file') || p.includes('File') || p === 'fileUrl') type = 'upload'
    else if (p.includes('Date') || p.includes('date')) type = 'date'
    else if (p === 'password') type = 'password'
    return { prop: c.prop, label: c.label, type, fileNameProp: p === 'fileUrl' ? 'fileName' : undefined }
  })
})

function reload() {
  crud.value?.load?.()
}

async function promptText(title, label = '说明') {
  const { value } = await ElMessageBox.prompt(label, title)
  return value
}

function rowActions(row) {
  const name = feat.value?.name || ''
  const path = feat.value?.path || ''
  const acts = []

  if (name === '标识审核' || path.includes('/trace/applies')) {
    if (row.status === 'PENDING' || row.status === 'SUBMITTED') {
      acts.push({
        label: '通过',
        onClick: async () => {
          await http.post(`/trace/applies/${row.id}/audit`, { approved: true })
          ElMessage.success('已通过')
          reload()
        },
      })
      acts.push({
        label: '驳回',
        onClick: async () => {
          await http.post(`/trace/applies/${row.id}/audit`, { approved: false, opinion: '驳回' })
          ElMessage.success('已驳回')
          reload()
        },
      })
    }
    if (row.status === 'APPROVED' || row.status === 'PASSED') {
      acts.push({
        label: '分发标识',
        onClick: async () => {
          await http.post(`/trace/applies/${row.id}/issue`)
          ElMessage.success('已分发')
          reload()
        },
      })
    }
  }

  if (path.includes('/quality/rectifications')) {
    if (auth.portal === 'ENT' && (row.status === 'PENDING' || row.status === 'ISSUED')) {
      acts.push({
        label: '接收',
        onClick: async () => {
          await http.post(`/quality/rectifications/${row.id}/accept`)
          ElMessage.success('已接收')
          reload()
        },
      })
      acts.push({
        label: '回复',
        onClick: async () => {
          const reply = await promptText('整改回复', '回复内容')
          await http.post(`/quality/rectifications/${row.id}/reply`, { reply })
          ElMessage.success('已回复')
          reload()
        },
      })
    }
    if (auth.portal === 'GOV' && (row.status === 'REPLIED' || row.status === 'DONE')) {
      acts.push({
        label: '复核通过',
        onClick: async () => {
          await http.post(`/quality/rectifications/${row.id}/review`, { approved: true })
          ElMessage.success('复核通过')
          reload()
        },
      })
    }
  }

  if (path.includes('/effluent/dispatches')) {
    if (row.status === 'PENDING') {
      acts.push({
        label: '接收',
        onClick: async () => {
          await http.post(`/effluent/dispatches/${row.id}/accept`)
          ElMessage.success('已接收')
          reload()
        },
      })
    }
    if (row.status === 'ACCEPTED' || row.status === 'PENDING') {
      acts.push({
        label: '反馈',
        onClick: async () => {
          const feedback = await promptText('调度反馈', '反馈内容')
          await http.post(`/effluent/dispatches/${row.id}/feedback`, { feedback })
          ElMessage.success('已反馈')
          reload()
        },
      })
    }
  }

  if (path.includes('/effluent/rectifications') && (row.status === 'PENDING' || row.status === 'DOING')) {
    acts.push({
      label: '回复',
      onClick: async () => {
        const reply = await promptText('尾水整改回复', '回复内容')
        await http.post(`/effluent/rectifications/${row.id}/reply`, { reply })
        ElMessage.success('已回复')
        reload()
      },
    })
  }

  if (path.includes('/iot/alarms') && (row.status === 'OPEN' || row.status === 'PENDING')) {
    acts.push({
      label: '确认',
      onClick: async () => {
        await http.post(`/iot/alarms/${row.id}/ack`)
        ElMessage.success('已确认')
        reload()
      },
    })
    acts.push({
      label: '关闭',
      onClick: async () => {
        await http.post(`/iot/alarms/${row.id}/close`)
        ElMessage.success('已关闭')
        reload()
      },
    })
  }

  if (path.includes('/ledger/after-sales') && (row.status === 'OPEN' || row.status === 'PENDING')) {
    acts.push({
      label: '处理',
      onClick: async () => {
        await http.post(`/ledger/after-sales/${row.id}/handle`)
        ElMessage.success('已处理')
        reload()
      },
    })
  }

  if (!acts.length) return null
  return acts
}
</script>

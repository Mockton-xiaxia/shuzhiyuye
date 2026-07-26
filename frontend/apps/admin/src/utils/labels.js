/** 枚举值 → 中文展示（对齐现网工作台/列表） */
export const BIZ_TYPE_LABELS = {
  TRACE_APPLY: '标识申请审核',
  EF_RECTIFICATION_REVIEW: '尾水整改待验收',
  QA_RECTIFICATION_REVIEW: '质量整改待验收',
  POND_AUDIT: '塘口信息审核',
  INFO_SUBMIT: '信息报送审核',
  EF_PLAN: '尾水排放计划',
  QA_INSPECTION: '质量抽检',
  DISPATCH: '指挥调度',
  ALARM: '设备预警',
}

export const STATUS_LABELS = {
  PENDING: '待处理',
  DONE: '已完成',
  OPEN: '待处理',
  CLOSED: '已关闭',
  DRAFT: '草稿',
  APPROVED: '已通过',
  SUBMITTED: '已提交',
  REJECTED: '已驳回',
  PASSED: '已通过',
  ISSUED: '已下发',
  REPLIED: '已回复',
  DOING: '处理中',
  ACCEPTED: '已接收',
}

export function labelOf(map, value, fallback = '-') {
  if (value == null || value === '') return fallback
  return map[value] || String(value)
}

export function bizTypeLabel(v) {
  return labelOf(BIZ_TYPE_LABELS, v, v)
}

export function statusLabel(v) {
  return labelOf(STATUS_LABELS, v, v)
}

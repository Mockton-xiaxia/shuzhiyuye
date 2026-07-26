# API 接口文档

> 自动生成 · 前缀 `/api/v1` · 2026-07-26

## 在线文档

启动后端后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 认证

```http
POST /api/v1/auth/login
Content-Type: application/json

{"username":"gov_admin","password":"123456"}
```

响应 `data.accessToken` 用于后续请求：

```
Authorization: Bearer <accessToken>
```

## 演示账号

| 用户名 | 密码 | 门户 |
|--------|------|------|
| gov_admin | 123456 | 区县 GOV |
| ent_admin | 123456 | 企业 ENT |

## 接口清单

### analytics-cms

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/analytics/cockpit` | Cockpit |
| GET | `/analytics/cockpit/town-points` | Cockpit Town Points |
| GET | `/analytics/enterprise-screen` | Ent Screen |
| GET | `/analytics/resources` | Resource Stats |
| GET | `/cms/articles` | Articles |
| GET | `/cms/categories` | Cms Categories |
| POST | `/cms/categories` | Create Category |
| GET | `/cms/videos` | Cms Videos |
| POST | `/cms/videos` | Create Video |
| GET | `/specialty/salamander` | Salamander |

### breeding

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/breeding/activities` | Activities |
| POST | `/breeding/activities` | Create Activity |
| PUT | `/breeding/activities/{aid}` | Update Activity |
| GET | `/breeding/batches` | Batches |
| POST | `/breeding/batches` | Create Batch |
| PUT | `/breeding/batches/{bid}` | Update Batch |
| GET | `/breeding/batches/{bid}/timeline` | Timeline |
| POST | `/breeding/harvests` | Harvest |
| GET | `/breeding/sales` | Sales |
| POST | `/breeding/sales` | Create Sale |
| PUT | `/breeding/sales/{sid}` | Update Sale |

### circulation

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/circulation/sales-orders` | Sales Orders |
| POST | `/circulation/sales-orders` | Create Order |
| POST | `/circulation/sales-orders/{oid}/cancel` | Cancel Order |
| POST | `/circulation/sales-orders/{oid}/confirm` | Confirm Order |
| POST | `/circulation/sales-orders/{oid}/fulfill` | Fulfill Order |
| GET | `/circulation/transports` | Transports |
| POST | `/circulation/transports` | Create Transport |
| PUT | `/circulation/transports/{tid}` | Update Transport |
| POST | `/circulation/transports/{tid}/arrive` | Arrive Transport |
| POST | `/circulation/transports/{tid}/depart` | Depart Transport |

### disease

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/disease/alerts` | Alerts |
| POST | `/disease/alerts` | Create Alert |
| PUT | `/disease/alerts/{aid}` | Update Alert |
| GET | `/disease/diagnosis-links` | Diagnosis Links |
| GET | `/disease/reports` | Reports |
| POST | `/disease/reports` | Create Report |

### domestication

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/specialty/domestication/economics` | Domestication Economics |
| GET | `/specialty/domestication/logs` | List Logs |
| POST | `/specialty/domestication/logs` | Create Log |
| PUT | `/specialty/domestication/logs/{lid}` | Update Log |
| DELETE | `/specialty/domestication/logs/{lid}` | Delete Log |
| GET | `/specialty/domestication/plots` | List Plots |
| POST | `/specialty/domestication/plots` | Create Plot |
| PUT | `/specialty/domestication/plots/{pid}` | Update Plot |
| DELETE | `/specialty/domestication/plots/{pid}` | Delete Plot |
| GET | `/specialty/domestication/stats` | Domestication Stats |

### effluent

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/effluent/dispatches` | Dispatches |
| POST | `/effluent/dispatches` | Create Dispatch |
| POST | `/effluent/dispatches/{did}/accept` | Accept Dispatch |
| POST | `/effluent/dispatches/{did}/feedback` | Feedback Dispatch |
| GET | `/effluent/facilities` | Facilities |
| POST | `/effluent/patrols` | Create Patrol |
| GET | `/effluent/patrols` | List Patrols |
| PUT | `/effluent/patrols/{pid}` | Update Patrol |
| GET | `/effluent/plans` | Plans |
| POST | `/effluent/plans` | Create Plan |
| GET | `/effluent/plans/unfiled-enterprises` | Unfiled Enterprises |
| PUT | `/effluent/plans/{pid}` | Update Plan |
| POST | `/effluent/plans/{pid}/file` | File Plan |
| POST | `/effluent/plans/{pid}/reject` | Reject Plan |
| POST | `/effluent/plans/{pid}/submit` | Submit Plan |
| GET | `/effluent/rectifications` | Ef Rects |
| POST | `/effluent/rectifications` | Create Ef Rect |
| POST | `/effluent/rectifications/{rid}/accept` | Accept Ef Rect |
| POST | `/effluent/rectifications/{rid}/reply` | Reply Ef Rect |
| POST | `/effluent/rectifications/{rid}/review` | Review Ef Rect |
| GET | `/effluent/waters` | Waters |
| POST | `/effluent/waters` | Create Water |
| PUT | `/effluent/waters/{water_id}` | Update Water |

### effluent-gis

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/effluent/discharge-plans/map` | Get Discharge Plans Map |
| POST | `/effluent/facilities` | Create Facility |
| GET | `/effluent/facilities/geojson` | Get Facilities Geojson |
| POST | `/effluent/facilities/{id}/check-outlet` | Check Outlet In Facility |
| GET | `/effluent/facilities/{id}/nearby-ponds` | Get Nearby Ponds |

### feature-fill

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/effluent/policies` | Effluent Policies |
| POST | `/effluent/policies` | Create Effluent Policy |
| PUT | `/effluent/policies/{pid}` | Update Effluent Policy |
| POST | `/feature/batch-delete` | Feature Batch Delete |
| GET | `/feature/demo` | Feature Demo |
| PUT | `/feature/update` | Feature Update |
| GET | `/iot/water-lab` | Water Lab |
| GET | `/iot/weather` | Iot Weather |
| GET | `/ledger/analysis` | Ledger Analysis |
| GET | `/ledger/budgets` | Ledger Budgets |
| POST | `/ledger/budgets` | Create Budget |
| GET | `/ledger/fees` | Ledger Fees |
| GET | `/ledger/portrait` | Ledger Portrait |
| GET | `/ledger/purchase-history` | Purchase History |
| GET | `/quality/stats-records` | Quality Stats Records |
| GET | `/specialty/disease-tests` | Disease Tests |
| POST | `/specialty/disease-tests` | Create Disease Test |
| GET | `/specialty/domestication-logs` | Domestication Logs Legacy |
| POST | `/specialty/domestication-logs` | Create Dom Log |
| GET | `/specialty/domestication-plots` | Domestication Plots Legacy |
| POST | `/specialty/domestication-plots` | Create Plot Legacy |
| GET | `/specialty/processing` | Processing |
| POST | `/specialty/processing` | Create Processing |
| GET | `/specialty/transports` | Specialty Transports |
| POST | `/specialty/transports` | Create Specialty Transport |
| GET | `/trace/label-stats` | Trace Label Stats |
| GET | `/wms/warehouse-equip` | Warehouse Equip |

### iot

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/iot/alarms` | Alarms |
| POST | `/iot/alarms/{aid}/ack` | Ack Alarm |
| POST | `/iot/alarms/{aid}/close` | Close Alarm |
| GET | `/iot/cameras` | Cameras |
| POST | `/iot/cameras` | Create Camera |
| PUT | `/iot/cameras/{cid}` | Update Camera |
| DELETE | `/iot/cameras/{cid}` | Delete Camera |
| POST | `/iot/cameras/{cid}/assign` | Assign Camera |
| GET | `/iot/cameras/{cid}/play-url` | Play Url |
| POST | `/iot/commands` | Send Command |
| GET | `/iot/commands` | Command Logs |
| GET | `/iot/devices` | Devices |
| GET | `/iot/ezviz/config` | Get Ezviz Config |
| PUT | `/iot/ezviz/config` | Put Ezviz Config |
| POST | `/iot/ezviz/test` | Test Ezviz |
| GET | `/iot/rules` | List Rules |
| POST | `/iot/rules` | Create Rule |
| PUT | `/iot/rules/{rid}` | Update Rule |
| GET | `/iot/strategies` | Strategies |
| POST | `/iot/strategies` | Create Strategy |
| POST | `/iot/telemetry` | Ingest Telemetry |
| GET | `/iot/telemetry` | List Telemetry |
| GET | `/map/layers` | Map Layers |

### iot-telemetry

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/iot/telemetry/aggregated` | Get Aggregated Telemetry |
| GET | `/iot/telemetry/anomalies` | Detect Anomalies |
| GET | `/iot/telemetry/latest` | Get Latest Telemetry |
| GET | `/iot/telemetry/statistics` | Get Statistics |

### ops

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/inputs/items` | Items |
| POST | `/inputs/items` | Create Item |
| GET | `/inputs/suppliers` | Suppliers |
| POST | `/inputs/suppliers` | Create Supplier |
| GET | `/ledger/after-sales` | After Sales |
| POST | `/ledger/after-sales` | Create After Sale |
| POST | `/ledger/after-sales/{aid}/handle` | Handle After Sale |
| GET | `/ledger/contracts` | Contracts |
| POST | `/ledger/contracts` | Create Contract |
| GET | `/ledger/customers` | Customers |
| POST | `/ledger/customers` | Create Customer |
| GET | `/ledger/entries` | Entries |
| POST | `/ledger/entries` | Create Entry |
| GET | `/wms/inbounds` | Inbounds |
| POST | `/wms/inbounds` | Create Inbound |
| GET | `/wms/outbounds` | Outbounds |
| POST | `/wms/outbounds` | Create Outbound |
| GET | `/wms/stocks` | Stocks |
| POST | `/wms/stocks/in` | Stock In |
| GET | `/wms/stocktakes` | Stocktakes |
| POST | `/wms/stocktakes` | Create Stocktake |
| POST | `/wms/stocktakes/{sid}/post` | Post Stocktake |
| GET | `/wms/warehouses` | Warehouses |
| POST | `/wms/warehouses` | Create Warehouse |

### party-gis

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/party/enterprises` | List Enterprises |
| POST | `/party/enterprises` | Create Enterprise |
| GET | `/party/enterprises-export` | Export Enterprises |
| POST | `/party/enterprises-import` | Import Enterprises |
| GET | `/party/enterprises-import-template` | Enterprises Import Template |
| POST | `/party/enterprises/batch-delete` | Batch Delete Enterprises |
| GET | `/party/enterprises/{eid}` | Get Enterprise |
| PUT | `/party/enterprises/{eid}` | Update Enterprise |
| DELETE | `/party/enterprises/{eid}` | Delete Enterprise |
| GET | `/party/gis/layers` | Get Gis Layers |
| GET | `/party/ponds` | List Ponds |
| POST | `/party/ponds` | Create Pond |
| POST | `/party/ponds/batch-audit` | Batch Audit Ponds |
| GET | `/party/ponds/geojson-template` | Ponds Geojson Template |
| POST | `/party/ponds/import-geojson` | Import Geojson |
| GET | `/party/ponds/spatial-query` | Spatial Query |
| POST | `/party/ponds/validate-geometry` | Validate Geometry |
| GET | `/party/ponds/{pid}` | Get Pond |
| PUT | `/party/ponds/{pid}` | Update Pond |
| POST | `/party/ponds/{pid}/audit` | Audit Pond |
| POST | `/party/ponds/{pid}/submit` | Submit Pond |
| GET | `/party/regions/tree` | Region Tree |
| GET | `/party/staffs` | List Staffs |
| POST | `/party/staffs` | Create Staff |
| PUT | `/party/staffs/{sid}` | Update Staff |

### platform

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | Login |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Me |
| GET | `/messages` | Messages |
| POST | `/platform/upload` | Upload File |
| GET | `/system/menus/tree` | Menu Tree |
| GET | `/todos` | List Todos |
| POST | `/todos/{todo_id}/done` | Done Todo |

### quality

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/quality/inspections` | Inspections |
| POST | `/quality/inspections` | Create Inspection |
| POST | `/quality/inspections/{iid}/issue-rect` | Issue Rect From Inspection |
| POST | `/quality/inspections/{iid}/submit` | Submit Inspection |
| GET | `/quality/labs` | Labs |
| POST | `/quality/labs` | Create Lab |
| PUT | `/quality/labs/{lid}` | Update Lab |
| GET | `/quality/policies` | Policies |
| POST | `/quality/policies` | Create Policy |
| PUT | `/quality/policies/{pid}` | Update Policy |
| GET | `/quality/rectifications` | Rectifications |
| POST | `/quality/rectifications/{rid}/accept` | Accept Rect |
| POST | `/quality/rectifications/{rid}/reply` | Reply Rect |
| POST | `/quality/rectifications/{rid}/review` | Review Rect |
| GET | `/quality/self-checks` | Self Checks |
| POST | `/quality/self-checks` | Create Self Check |
| GET | `/quality/stats` | Quality Stats |

### supply

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/supply/listings` | Listings |
| POST | `/supply/listings` | Create Listing |
| GET | `/supply/markets` | Markets |
| POST | `/supply/markets` | Create Market |
| GET | `/supply/prices` | Prices |
| POST | `/supply/prices` | Create Price |

### system

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/system/audit-logs` | Audit Logs |
| POST | `/system/dict-items` | Create Dict Item |
| GET | `/system/dict-types` | Dict Types |
| POST | `/system/dict-types` | Create Dict Type |
| GET | `/system/dicts/{code}/items` | Dict Items |
| GET | `/system/menus` | List Menus |
| GET | `/system/roles` | List Roles |
| GET | `/system/users` | List Users |
| POST | `/system/users` | Create User |
| PUT | `/system/users/{uid}` | Update User |
| PUT | `/system/users/{uid}/reset-password` | Reset Password |
| PUT | `/system/users/{uid}/status` | User Status |

### trace

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/public/trace/{code}` | Public Trace |
| GET | `/trace/applies` | List Applies |
| POST | `/trace/applies` | Create Apply |
| POST | `/trace/applies/{aid}/audit` | Audit Apply |
| POST | `/trace/applies/{aid}/issue` | Issue Codes |
| POST | `/trace/applies/{aid}/submit` | Submit Apply |
| GET | `/trace/codes` | List Codes |
| GET | `/trace/issues` | List Issues |
| GET | `/trace/stats` | Trace Stats |

### uav

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/uav/missions` | List Missions |
| POST | `/uav/missions` | Create Mission |
| PUT | `/uav/missions/{mid}` | Update Mission |
| DELETE | `/uav/missions/{mid}` | Delete Mission |
| GET | `/uav/pilots` | List Pilots |
| POST | `/uav/pilots` | Create Pilot |
| PUT | `/uav/pilots/{pid}` | Update Pilot |
| DELETE | `/uav/pilots/{pid}` | Delete Pilot |
| GET | `/uav/stats` | Uav Stats |

## 核心业务域

| 域 | 前缀 | 说明 |
|----|------|------|
| 平台 | `/auth`, `/todos` | 登录、待办 |
| 系统 | `/system` | 用户、角色 |
| 主体 | `/party` | 企业、塘口、GIS、人员 |
| 质量 | `/quality` | 政策、抽检、整改 |
| 追溯 | `/trace` | 标识申请、分发 |
| 尾水 | `/effluent` | 计划、巡检、调度 |
| 养殖 | `/breeding` | 批次、农事、销售 |
| 物联 | `/iot` | 设备、摄像头、告警 |
| 仓储 | `/wms`, `/inputs` | 仓库、库存、投入品 |
| 账本 | `/ledger` | 客户、合同、记账 |
| 流通 | `/circulation` | 销售订单、运输 |
| 供应 | `/supply` | 渔需推介、行情 |
| 资讯 | `/cms` | 文章、视频 |
| 分析 | `/analytics` | 驾驶舱、企业大屏 |
| 通用 | `/feature/update` | CrudPage 编辑兜底 |

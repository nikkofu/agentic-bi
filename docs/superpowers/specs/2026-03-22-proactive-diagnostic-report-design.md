# Proactive Diagnostic Report Design

**Date:** 2026-03-22
**Project:** agentic-bi
**Scope:** Phase 2 Analyst 方向的首个结构化诊断报告闭环
**Primary user:** 业务负责人、销售分析用户
**Primary success criterion:** 从主动洞察卡片或直接请求都能生成并查看一份可审计、可解释、可多页面浏览的诊断报告快照

---

## 1. 背景与目标

当前仓库已经具备两层基础能力：
- Phase 1 销售副驾：自然语言问答、RBAC、安全审计、自动图表报表协议
- 主动洞察基础扩展：规则触发、单层归因、异常卡片生成与列表 API

但系统还停留在“发现异常并生成卡片”的层级，没有进入 Phase 2 Analyst 所要求的“结构化业务诊断报告”能力。当前缺口主要有：
- insight card 只能表达异常摘要，不能承载完整诊断上下文
- 没有统一的诊断报告对象、快照、详情 API 和 viewer 入口
- 用户无法从异常卡片继续深入阅读结构化诊断结果
- 现有 auto-reporting viewer 已支持多页 `DashboardSpec`，但还没有面向 Analyst 诊断报告的装配逻辑

本设计目标是新增一条受控、快照型、双入口的诊断报告主线：
- 支持从 `insight card -> diagnostic report`
- 支持直接请求生成 `diagnostic report`
- 报告结果以结构化快照固化，便于审计与复现
- 报告渲染继续复用现有 `DashboardSpec + viewer`
- 只暴露结构化诊断摘要，不暴露原始 chain-of-thought

---

## 2. 方案对比与选型

### 方案 A（选定）：复用 reporting protocol + 快照型诊断报告 + 双入口
- 后端新增诊断报告构建器与诊断 dashboard 组装器
- 报告本体继续使用 `DashboardSpec`
- insight 触发时同步生成报告快照
- 同时开放 direct generate 接口

优点：
- 复用现有 viewer、dashboard persistence、RBAC、audit
- 交付路径最短，系统边界最统一
- “自动图形报表”与“结构化诊断报告”在同一协议下演进

缺点：
- 需要给现有 reporting 协议补少量 diagnostic metadata
- viewer 需要从“页面平铺”提升到“多页面导航”

### 方案 B：单独 diagnostic schema + 单独 viewer
- 后端和前端都为 Analyst 报告单独建模

优点：
- 诊断语义最纯

缺点：
- 重复建设明显
- 一轮内会同时新增协议、渲染器、持久化、API、路由，成本偏高

### 方案 C：内部 diagnostic schema，外部映射成 `DashboardSpec`
- 后端先产出内部语义模型，再映射到 dashboard protocol

优点：
- 中长期内部模型更干净

缺点：
- 本阶段多一层转换与调试面
- 当前收益小于复杂度

### 选型结论

选择 **方案 A**。

原因：
- 当前产品阶段最重要的是尽快把“发现异常”升级成“可消费的诊断报告”
- 仓库里已经具备 auto-reporting 协议和 viewer，这些资产应直接复用
- Phase 2 Analyst 的第一步应优先建立稳定快照、统一 viewer、清晰审计边界，而不是重新发明一套展示协议

---

## 3. 范围与非目标

### 3.1 本设计覆盖
- 诊断报告双入口
- 快照型报告对象与持久化关系
- 基于现有 reporting protocol 的多页面诊断报告装配
- insight card 与 report/dashboard 的关联
- 报告详情 API 与 viewer 路由
- 报告中的结构化诊断摘要、安全边界与测试策略

### 3.2 本设计不覆盖
- 导出 PDF / 静态文件
- 分享链接 / 跨用户共享
- 自动刷新旧报告快照
- 多层、多轮、开放式推理过程展示
- Phase 3 的行动执行与审批流
- 复杂模型驱动归因或诊断编排

本阶段聚焦的是：
**“从异常卡片或直接请求生成一份结构化、可多页面浏览的诊断报告快照。”**

---

## 4. 总体架构

### 4.1 统一报告内核

系统新增统一的 `diagnostic_report_builder` / `diagnostic_dashboard_assembler` 内核，分别负责：
- 构建诊断报告的语义上下文、摘要、结论、建议
- 将诊断素材组装成多页 `DashboardSpec`

两类入口都走这一内核：
- `insight card -> report`
- `direct generate -> report`

### 4.2 报告仍是受控的 `DashboardSpec`

诊断报告本体不新建渲染协议，而是定义为一类带有 diagnostic metadata 的 `DashboardSpec`：
- `report_kind = diagnostic`
- `source_kind = insight_card | on_demand`
- `source_ref`
- `snapshot_time`
- `diagnostic_summary`
- `recommended_questions`

这样做的结果是：
- viewer 不必重写
- dashboard persistence 可继续复用
- 报告与普通 auto-reporting dashboard 可以共享协议底座

### 4.3 多页面 viewer

viewer 从当前的“平铺 pages”升级为“应用内多页面导航”，但仍使用现有 widget renderer。

报告 v1 固定三页：
- `Overview`
- `Drivers`
- `Actions`

这保证了信息架构稳定，不会在第一版就变成开放式报表编辑器。

---

## 5. 数据模型设计

### 5.1 新增报告元信息层

新增 `diagnostic_report_models.py`，定义以下对象：

#### `DiagnosticReport`
- `id`
- `version`
- `tenant_id`
- `principal_id`
- `source_kind`
- `source_ref`
- `snapshot_time`
- `status`
- `summary`
- `findings[]`
- `recommendations[]`
- `dashboard_id`
- `report_intent_id`
- `trace`

#### `DiagnosticReportSummary`
- `title`
- `subtitle`
- `metric`
- `scope`
- `time_window`
- `severity`
- `headline`

#### `DiagnosticFinding`
- `kind`
- `title`
- `statement`
- `evidence_refs[]`

#### `DiagnosticRecommendation`
- `kind`
- `label`
- `question`
- `rationale`

设计原则：
- 这些对象是“报告元信息层”，不是新的渲染协议
- 报告元信息和 dashboard snapshot 要同时落库
- dashboard 负责渲染，report metadata 负责治理、检索、详情和跨入口引用

### 5.2 与现有 reporting protocol 的关系

诊断报告继续复用：
- `ReportIntent`
- `DashboardSpec`
- `DashboardPage`
- `DashboardSection`
- `DashboardWidget`

但需要在 `DashboardSpec` 层容纳少量 metadata，或者在 `DiagnosticReport` 中持有相关摘要并与 `dashboard_id` 关联。

### 5.3 快照关系模型

持久化关系建议固定为：

`insight_card -> diagnostic_report -> dashboard_snapshot`

说明：
- 一个 insight card 在本阶段只绑定一份默认报告快照
- 一个 direct generate 请求会生成新的 `diagnostic_report`
- 每个 `diagnostic_report` 绑定一份持久化 dashboard snapshot
- 默认不覆盖旧报告，不做“就地刷新”

---

## 6. 页面信息架构

### 6.1 Overview
- 异常摘要
- KPI 指标卡
- 主趋势图
- 报告生成时间 / 作用域 / 严重级别

### 6.2 Drivers
- 主归因图或表
- 结构化诊断要点
- 关键证据引用（规则来源、查询来源、窗口说明）

### 6.3 Actions
- 建议追问
- 建议后续动作
- 相关治理上下文（trace、rule、time window、scope）

设计原则：
- 第一版每页职责单一
- 不引入自由排版编辑能力
- 保证 viewer 在移动端和桌面端都能顺序浏览

---

## 7. 接口设计

### 7.1 Insight 关联详情

保留 `GET /v1/insights/cards`，但每个 item 需增加：
- `report_id`
- `dashboard_id`
- `detail_url`

新增：
- `GET /v1/insights/cards/{card_id}` 或等价 detail endpoint
  - 返回 insight card 详情
  - 返回关联报告摘要

### 7.2 Diagnostic Reports API

建议新增独立 router，例如 `src/app/api/reports.py`，而不是继续把所有逻辑堆进 `reporting.py`。

新增接口：
- `POST /v1/reports:generate`
- `GET /v1/reports/{report_id}`

`POST /v1/reports:generate` 支持两类输入：
- 基于已有 insight/anomaly 上下文
- 基于显式 metric/scope/time_window 的 direct generate

返回内容建议至少包括：
- `report_id`
- `dashboard_id`
- `report_summary`
- `dashboard`

### 7.3 Viewer 路由

前端建议补齐：
- `/reports/:reportId`
- `/dashboards/:dashboardId`

其中：
- `/reports/:reportId` 用于 report 详情与治理语义入口
- `/dashboards/:dashboardId` 继续作为统一渲染入口

---

## 8. 端到端数据流

### 8.1 Insight Card 入口
1. 监控任务检测到 anomaly
2. 生成 anomaly event
3. 生成 insight card
4. 同步构建 `DiagnosticReportIntent`
5. 执行受控查询，收集趋势、比较、归因等诊断素材
6. 组装多页 `DashboardSpec`
7. 持久化 `diagnostic_report + dashboard snapshot`
8. 将 `report_id/dashboard_id` 回填到 insight card
9. 返回列表时暴露详情入口

### 8.2 Direct Generate 入口
1. 收到 `POST /v1/reports:generate`
2. 构建 `DiagnosticReportIntent`
3. 执行受控查询
4. 组装报告 dashboard
5. 持久化报告快照
6. 返回 viewer 可直接消费的 payload

### 8.3 读取流程
1. 用户从 insight card 或直接链接进入
2. 后端基于 `report_id` 做权限检查
3. 返回 report metadata
4. viewer 通过 `dashboard_id` 或直接嵌入 dashboard payload 渲染

---

## 9. 安全、治理与解释边界

### 9.1 RBAC
- 所有 reports 继承当前 `principal_id + role_scope + row_level_policy_ref`
- 报告创建时固化 permission context
- 报告读取时必须校验上下文一致性
- 不允许通过旧报告读取到当前不再有权限的数据

### 9.2 审计
- 记录 report generation 入口来源
- 记录使用到的 query refs / source refs
- 记录 `report_id`、`dashboard_id`、`trace_id`
- 记录 permission context 快照

### 9.3 解释边界

只允许展示：
- 结论摘要
- 指标变化
- 归因线索
- 查询/规则来源
- 建议追问与建议动作

不允许展示：
- 原始 chain-of-thought
- 未经过滤的中间推理文本
- 与用户权限无关的额外数据线索

本设计默认采用：
**“结构化诊断摘要，不暴露原始推理过程。”**

---

## 10. 错误处理与回退策略

### 10.1 数据不足
- 可返回部分报告
- 在 `Drivers` 或 `Actions` 页展示 `insufficient_data`
- 不因为某个归因失败而整份报告报错

### 10.2 报告构建失败
- insight card 流程允许“卡片成功、报告失败”
- 失败必须写审计
- card detail 中可提示报告暂不可用

### 10.3 Viewer 回退
- 若 report metadata 可读但 dashboard 缺失，返回明确错误态
- 若 dashboard 存在但 metadata 缺失，视为数据完整性问题并阻断展示

---

## 11. 测试与验收

### 11.1 后端单测
- `DiagnosticReport` 模型 contract
- `diagnostic_report_builder` 结构化 summary / findings / recommendations
- `diagnostic_dashboard_assembler` 是否稳定产出 3 页 dashboard

### 11.2 后端集成测试
- `insight -> report snapshot -> dashboard fetch`
- `POST /v1/reports:generate`
- `GET /v1/reports/{report_id}`
- RBAC 下 report/detail/dashboard 的可见性
- 审计记录是否包含 `report_id/dashboard_id/trace_id`

### 11.3 前端测试
- viewer 多页面导航切换
- `/reports/:reportId` 页面装载
- insight 入口跳到诊断报告 viewer
- 诊断页的结构化摘要与 widget 渲染

### 11.4 验收标准
- 能从 insight card 打开诊断报告
- 能直接生成一份诊断报告
- 诊断报告以快照方式固化并可重复读取
- viewer 能稳定浏览至少 3 页内容
- 现有 chat / reporting / insight 基础链路回归通过

---

## 12. 非目标与后续演进

### 本阶段不做
- 导出
- 分享
- 报告刷新/重算
- 自由编排编辑器
- 复杂模型驱动诊断

### 下一阶段自然延伸
- report refresh / regenerate
- 导出 PDF / 静态快照
- 分享与权限化访问入口
- 更丰富的诊断 finding types
- report center / insight center 前端工作台

---

## 13. 里程碑建议

- **M1：Report metadata 与快照持久化打通**
- **M2：Insight card 入口与 direct generate 入口打通**
- **M3：多页面 viewer 与 report detail API 打通**
- **M4：RBAC / 审计 / 回归测试达标**

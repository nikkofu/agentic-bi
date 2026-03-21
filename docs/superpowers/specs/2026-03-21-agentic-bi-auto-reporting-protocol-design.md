# Agentic BI Auto Reporting Protocol Design

**Date:** 2026-03-21
**Project:** agentic-bi
**Scope:** 自动图形报表与未来 Dashboard 设计器的协议底座
**Primary user:** 业务分析用户、Dashboard 设计者、前后端实现者
**Primary success criterion:** 用一套稳定协议同时支撑自动报表、可保存 Dashboard、后续完整设计器，而不绑定单一图表引擎

---

## 1. 背景与目标

当前分支已经具备 Phase 1 销售副驾的问答能力，但返回结果仍停留在“自然语言答案 + 轻量 chart JSON”层级，尚未形成类似 DataBI 的自动图形报表产品能力。

现状问题：
- 后端只输出有限的 `chart.type` 与 `chart.data`
- 没有真正的报表 Viewer / Dashboard / 设计器前端
- 没有可保存、可版本化、可编辑的运行时文档格式
- 没有把“推理过程”以安全、结构化的方式转成报表解释层

本设计不直接实现完整通用 BI 平台，而是先定义一套协议底座，满足以下目标：
- 支持“问答后自动生成单页图形报表”
- 支持将自动报表保存为 Dashboard
- 为后续拖拽式 Dashboard 设计器保留稳定接口
- 让主协议保持 `engine-agnostic`，通过 adapter 接入具体图表引擎
- 以结构化 explanation 替代原始 chain-of-thought 暴露

---

## 2. 方案对比与选型

### 方案 A：单一超级文档
一个 JSON 同时承载语义查询、运行时页面、编辑器状态、图表引擎私有配置。

优点：
- 起步快，demo 容易产出
- 前后端传一个文档即可

缺点：
- 运行时与编辑态强耦合
- 难以版本化、验证和审计
- 后续接第二种 renderer 成本高
- 设计器实现细节污染稳定保存格式

### 方案 B：两层协议
拆成 `dashboard_spec` 和 `editor_state` 两层，语义查询直接嵌在 widgets 中。

优点：
- 比单一文档清晰
- 运行态与编辑态至少分离

缺点：
- 自动报表生成与设计器仍未真正解耦
- widget 内嵌语义层，后续复用和迁移成本高
- 通常会在下一阶段被迫再拆一次

### 方案 C（选定）：三层协议
拆成 `report_intent`、`dashboard_spec`、`editor_state` 三层，并通过 renderer adapter 接入 ECharts 等具体图表库。

优点：
- 自动报表、保存后的 Dashboard、未来设计器共用同一底座
- 运行时格式与编辑器实现细节解耦
- 便于多 renderer、版本迁移、审计和验证
- 与未来通用数据接入层兼容

缺点：
- 第一版设计成本更高
- 需要明确层间边界和引用规则

### 选型结论
选择 **方案 C：三层协议**。

原因：
- 这是唯一能同时兼顾“自动报表产品化”和“完整 BI 设计器扩展性”的方案
- 可以把当前问答 MVP 结果逐步迁移为稳定的报表协议，而不是重做一套前端专用格式

---

## 3. 设计范围与非目标

### 3.1 本设计覆盖
- 三层协议的职责边界
- 最小对象模型
- 自动报表与设计器共享的数据流
- 协议相关 API 与存储边界
- renderer / 开源组件接入策略
- 分阶段落地建议

### 3.2 本设计不直接承诺实现
- 完整通用 BI 平台
- 任意 SQL 自助建模
- 多人实时协作编辑
- 跨租户分享与审批流
- 全量 renderer 生态同时接入

本设计的直接 planning 对象是：**协议底座与其第一阶段落地路径**，不是“一次性做完完整 BI 平台”。

---

## 4. 三层协议职责边界

### 4.1 `report_intent`
负责“为什么会生成这份报表”以及“它所依赖的业务语义”。

职责：
- 记录用户问题或保存后的分析目标
- 保存语义查询定义：指标、维度、筛选、时间范围、比较方式、排序、限制
- 保存自动编排时的 explanation 来源
- 保存租户、数据集、权限上下文、trace 信息

不负责：
- 页面栅格布局
- 拖拽态和选中态
- 某个 renderer 的私有配置

### 4.2 `dashboard_spec`
负责“最终展示给用户什么”，是稳定的运行时文档格式。

职责：
- 保存 Dashboard 页面结构、Section、Widget、布局与交互
- 描述 widgets 如何绑定 `report_intent` 或物化结果
- 保存图表的抽象视觉语义，而非具体引擎配置
- 支持 Viewer 和未来设计器的共同消费

不负责：
- 撤销栈
- 面板展开状态
- 鼠标拖拽中的临时状态
- ECharts / Vega 的完整底层 spec 透传

### 4.3 `editor_state`
负责“设计器正在如何编辑这份 Dashboard”，是纯编辑期状态。

职责：
- 记录当前选中对象
- 记录拖拽过程中的临时布局与草稿
- 记录 undo/redo 历史与校验标记
- 记录视口、面板、编辑器 UI 状态

不负责：
- 作为运行时 Viewer 的必需输入
- 成为稳定发布格式的一部分

### 4.4 层间关系
三层关系固定为：

`report_intent -> dashboard_spec -> editor_state`

规则：
- `dashboard_spec` 可以引用 `report_intent` 或其执行结果
- `editor_state` 只引用 `dashboard_spec` 内的稳定节点 ID
- 禁止反向依赖，尤其禁止语义层引用前端 widget ID

---

## 5. 最小对象模型

### 5.1 `report_intent` 对象族

#### `ReportIntent`
- `id`
- `version`
- `tenant_id`
- `dataset_id`
- `source`
- `question`
- `goal`
- `semantic_queries[]`
- `explanations[]`
- `constraints`
- `trace`

#### `SemanticQuery`
- `id`
- `kind`
- `measures[]`
- `dimensions[]`
- `filters[]`
- `time`
- `comparison`
- `sort`
- `limit`
- `display_hint`

#### `ExplanationBlock`
- `id`
- `type`
- `title`
- `content`
- `evidence_refs[]`

设计原则：
- 一个 `ReportIntent` 可以包含多条 `SemanticQuery`
- explanation 必须是结构化摘要，不暴露原始 chain-of-thought

### 5.2 `dashboard_spec` 对象族

#### `DashboardSpec`
- `id`
- `version`
- `title`
- `description`
- `theme`
- `refresh_policy`
- `variables[]`
- `pages[]`
- `data_bindings[]`
- `interactions[]`

#### `Page`
- `id`
- `title`
- `layout`
- `sections[]`

#### `Section`
- `id`
- `title`
- `layout`
- `widgets[]`

#### `Widget`
- `id`
- `kind`
- `title`
- `subtitle`
- `layout`
- `binding`
- `presentation`
- `actions[]`
- `visibility_rule`

第一版稳定支持的 `Widget.kind`：
- `metric_card`
- `chart`
- `table`
- `text`
- `filter`
- `insight`

### 5.3 绑定模型

#### `WidgetBinding`
- `source_type`
- `source_ref`
- `materialization`
- `field_mapping`

`source_type` 第一版支持：
- `semantic_query`
- `materialized_result`
- `derived_view`

设计原则：
- widget 不内嵌完整查询定义
- 同一条 `SemanticQuery` 可以被多个 widgets 复用

### 5.4 图表抽象模型

#### `ChartPresentation`
- `family`
- `encodings`
- `stacking`
- `sorting`
- `legend`
- `axes`
- `annotations[]`
- `palette`
- `density`
- `renderer_hints`

第一版 `family` 建议支持：
- `line`
- `bar`
- `area`
- `pie`
- `scatter`
- `combo`
- `funnel`
- `radar`
- `treemap`
- `table_like`

`encodings` 采用角色式抽象：
- `x`
- `y`
- `color`
- `size`
- `series`
- `label`
- `tooltip`

规则：
- 主协议不直接存 ECharts option
- `renderer_hints` 只允许受控扩展，不能演化为任意透传口袋

### 5.5 交互模型

#### `Interaction`
- `id`
- `trigger`
- `source_widget_id`
- `target_scope`
- `effect`
- `payload`

第一版需要覆盖：
- 点击图例或图元触发联动过滤
- 时间范围切换刷新多个 widgets
- 页面内跳转或 drilldown

### 5.6 `editor_state` 最小模型

#### `EditorState`
- `document_id`
- `selection`
- `draft_layout_overrides`
- `panel_state`
- `history`
- `validation_markers`
- `viewport`

规则：
- `history`、`selection`、`panel_state` 不进入 `dashboard_spec`
- 用户显式保存前，布局改动只存在于草稿态

---

## 6. 端到端数据流

### 6.1 自动报表生成路径
1. 用户输入自然语言问题
2. 后端生成 `report_intent`
3. `report_intent` 产出 1 到多条 `semantic_query`
4. 查询执行层返回实时结果或物化结果
5. `report_assembler` 根据数据形态与 explanation 规则生成 `dashboard_spec`
6. renderer adapter 将抽象图表转为具体渲染配置
7. Viewer 渲染图形报表与 explanation widgets

### 6.2 设计器编辑路径
1. 前端加载 `dashboard_spec`
2. 前端恢复或创建 `editor_state`
3. 用户进行拖拽、改图型、改交互、改布局
4. 编辑中的变更先写入草稿态
5. 用户保存后，将确认的结构性变更写回 `dashboard_spec`
6. 若改动涉及语义层，则更新对应 `report_intent` 或新增 `semantic_query`
7. 保存后重新校验绑定和交互，并按需刷新结果

### 6.3 核心原则
- 自动报表和设计器共用同一条语义与渲染链路
- 系统不保留原始 chain-of-thought，只生成结构化 explanation
- 同一语义查询可以被多个 widgets 复用

---

## 7. 结果物化、缓存与解释策略

### 7.1 引用优先，物化按需
默认情况下，`dashboard_spec` 通过 `binding.source_ref` 指向 `semantic_query`，Viewer 在读取时执行实时查询或命中缓存。

以下场景允许物化：
- 自动报表首屏需要更快加载
- 结果集较大，表格需要分页或快照
- 需要保存“当时看到的结果”用于审计
- 同一结果被跨页面、跨 widgets 复用

#### `MaterializedResult`
- `id`
- `source_query_id`
- `schema`
- `rows`
- `summary`
- `cache_key`
- `freshness`
- `created_at`

### 7.2 结构化 explanation
前端展示 explanation 时只允许使用结构化摘要，包括：
- 查询目标
- 选择的指标、维度、时间范围
- 图表类型选择原因
- 关键发现
- 数据证据引用
- 风险与限制
- `trace_id`

禁止：
- 向用户直接暴露模型原始 chain-of-thought

---

## 8. API 边界

### 8.1 Intent API
- `POST /v1/report-intents:generate`
- `GET /v1/report-intents/{id}`
- `PATCH /v1/report-intents/{id}`

职责：
- 从自然语言问题或手工配置生成 / 更新 `report_intent`

### 8.2 Query / Materialization API
- `POST /v1/semantic-queries:execute`
- `GET /v1/materialized-results/{id}`
- `POST /v1/materialized-results:refresh`

职责：
- 执行语义查询
- 获取或刷新物化结果

### 8.3 Dashboard API
- `POST /v1/dashboards:assemble`
- `POST /v1/dashboards`
- `GET /v1/dashboards/{id}`
- `PATCH /v1/dashboards/{id}`
- `POST /v1/dashboards/{id}:duplicate`

职责：
- 自动组装运行时 Dashboard
- 保存、读取和复制 `dashboard_spec`

### 8.4 Editor Session API
- `GET /v1/dashboards/{id}/editor-state`
- `PUT /v1/dashboards/{id}/editor-state`
- `POST /v1/dashboards/{id}:validate`
- `POST /v1/dashboards/{id}:publish`

职责：
- 负责设计器草稿、校验与发布流程

### 8.5 与当前 `/v1/chat/query` 的关系
现有问答接口可以在第一阶段继续存在，但应逐步退化为 façade：
- `chat` 入口负责承接自然语言
- 底层执行改由 `report_intent + assemble dashboard` 链路完成

即：
- 保留兼容性
- 不再把未来协议设计建立在 `/v1/chat/query` 单一接口之上

---

## 9. 存储与版本化边界

第一版建议至少有以下实体：
- `report_intents`
- `semantic_queries`
- `dashboards`
- `dashboard_revisions`
- `editor_sessions`
- `materialized_results`
- `audit_events`

### 9.1 关键要求
- `dashboard_revisions` 必须存在，用于版本快照和回滚
- `editor_sessions` 与 `dashboard_revisions` 分离，分别代表草稿态与正式历史
- 三层协议对象都要显式带 `version`

### 9.2 推荐版本字段
- `report_intent.version`
- `dashboard_spec.version`
- `editor_state.version`

### 9.3 推荐 Dashboard 元信息
- `current_revision_id`
- `published_revision_id`
- `draft_revision_id`

---

## 10. Renderer 与开源组件接入策略

### 10.1 选型原则
- 主协议保持 `engine-agnostic`
- 通过 adapter 接入具体图表 renderer
- 第一 renderer 优先满足商业展示、图型覆盖和 Dashboard 体验

### 10.2 第一 renderer：Apache ECharts
选择理由：
- 图型覆盖全面，适合“各种各样的可视化效果”
- 适合作为自动报表 Viewer 和后续 Dashboard 的第一渲染引擎
- 对企业展示场景和组合图形更友好

### 10.3 第二 renderer 预留：Vega-Lite
Vega-Lite 适合作为未来声明式可视化 adapter 预留，但不作为第一阶段主 renderer。

### 10.4 设计器层与图表层分离
完整 BI 设计器不等于图表 renderer。

需要分层：
- 图表渲染：ECharts adapter
- 页面布局与拖拽：独立 grid / drag 方案
- 属性面板和字段映射面板：基于主协议自建编辑器

### 10.5 适配器职责
第一版建议拆成：
- `chart_normalizer`
- `chart_recommender`
- `echarts_adapter`

职责：
- 规范化数据表结构
- 根据意图和数据形态推荐图型
- 把抽象图表模型转为 ECharts option

---

## 11. 安全、权限与审计

由于长期目标是通用 BI 设计器，第一版协议层就要保留权限上下文：
- `tenant_id`
- `principal_id`
- `dataset_id`
- `role_scope`
- `row_level_policy_ref`

规则：
- 查询执行必须强制带权限上下文
- 保存或发布 Dashboard 时必须校验所引用数据集与字段权限
- explanation 与审计展示必须脱敏，不泄漏越权信息
- 所有自动生成、保存、发布、刷新动作都应进入 `audit_events`

---

## 12. 分阶段落地建议

### 阶段 1：协议底座 + 自动报表 Viewer
目标：
- 定义三层协议
- 新增 `assemble dashboard` 能力
- 新建只读 Viewer
- 接入 ECharts adapter
- 支持问答结果保存为 Dashboard
- 展示结构化 explanation

不做：
- 完整拖拽设计器
- 通用任意数据集接入
- 多人协作

### 阶段 2：Dashboard 编辑器
目标：
- 支持拖拽布局
- 支持增删改 widgets
- 支持基础交互配置
- 引入 `editor_state`、`validate`、`publish` 流程
- 支持 revisions 与模板复制

### 阶段 3：通用 BI 设计器与数据接入
目标：
- 数据集注册与语义建模
- 多主题域 Dashboard
- 更强 renderer 扩展
- 更完整的权限、协作与模板能力

---

## 13. 测试与验收建议

### 13.1 协议层测试
- schema 兼容性测试
- 版本升级 / 迁移测试
- 引用完整性测试
- 非法交互和循环依赖校验测试

### 13.2 渲染链路测试
- `dashboard_spec -> adapter -> renderer config` 契约测试
- 同一抽象图表在多数据形态下的图型推荐测试
- explanation widgets 的结构化渲染测试

### 13.3 存储与权限测试
- dashboard revision 回滚测试
- editor draft 与正式发布隔离测试
- 不同权限上下文下的查询与展示测试

### 13.4 第一阶段验收标准
- 现有问答结果可组装为单页 Dashboard
- Dashboard 可保存、读取、只读展示
- 抽象图表可稳定渲染到 ECharts
- explanation 以结构化方式展示，不暴露原始 chain-of-thought
- 当前协议可自然支撑下一阶段编辑器规划，而无需重做持久化格式

---

## 14. 实施边界与后续 planning 输入

本设计文档确认的是 **协议底座优先** 的路线，而不是直接交付完整 BI 设计器。

下一步 implementation planning 应围绕以下最小交付集合展开：
- 三层协议 schema 定义
- `assemble dashboard` 后端能力
- 兼容现有 `/v1/chat/query` 的迁移策略
- 自动报表 Viewer 前端
- ECharts adapter
- Dashboard 存储、读取与 revisions
- explanation widget 的结构化展示

后续 planning 不应把“任意数据源接入”和“完整通用 BI 设计器”与以上最小交付混为一个单计划执行。

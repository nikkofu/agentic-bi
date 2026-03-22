import type { DiagnosticReportDocument } from "../../types/reporting";

export const diagnosticReportFixture: DiagnosticReportDocument = {
  report: {
    id: "dr-1",
    version: "1.0",
    tenant_id: "t-1",
    principal_id: "u-1",
    source_kind: "insight_card",
    source_ref: "card-1",
    snapshot_time: "2026-03-23T08:00:00Z",
    status: "ready",
    summary: {
      title: "华东区毛利率异常诊断报告",
      subtitle: "last_month",
      metric: "gross_margin_rate",
      scope: { region: "华东" },
      time_window: "last_month",
      severity: "high",
      headline: "gross_margin_rate = 0.24",
    },
    findings: [
      {
        kind: "trend",
        title: "异常延续",
        statement: "华东区毛利率低于基线。",
        evidence_refs: ["trace-1"],
      },
    ],
    recommendations: [
      {
        kind: "question",
        label: "继续诊断",
        question: "是什么导致华东区毛利率下降？",
        rationale: "从驱动页继续分析。",
      },
    ],
    dashboard_id: "dash-dr-1",
    report_intent_id: "ri-dr-1",
    trace: { trace_id: "trace-1" },
  },
  dashboard: {
    id: "dash-dr-1",
    version: "1.0",
    title: "诊断报告仪表板",
    description: "Diagnostic report dashboard fixture",
    theme: {},
    refresh_policy: {},
    variables: [],
    data_bindings: [
      {
        id: "binding-overview",
        kind: "materialized_result",
        source_ref: "overview",
        value: 0.24,
        rows: [
          { month: "2026-01", value: 0.29 },
          { month: "2026-02", value: 0.27 },
          { month: "2026-03", value: 0.24 },
        ],
        insight: "毛利率连续走低。",
      },
      {
        id: "binding-drivers",
        kind: "materialized_result",
        source_ref: "drivers",
        rows: [
          { region: "华东", value: -0.06 },
          { region: "重点客户", value: -0.03 },
        ],
        insight: "Drivers fixture insight",
      },
      {
        id: "binding-actions",
        kind: "materialized_result",
        source_ref: "actions",
        text: "联系区域负责人并复核折扣策略。",
      },
    ],
    interactions: [],
    pages: [
      {
        id: "page-overview",
        title: "Overview",
        layout: {},
        sections: [
          {
            id: "section-overview",
            title: "Overview Section",
            layout: {},
            widgets: [
              {
                id: "widget-overview-metric",
                kind: "metric_card",
                title: "Overview KPI",
                presentation: {
                  family: "kpi",
                  variant: "primary",
                  config: { metric: "gross_margin_rate" },
                },
                binding: {
                  source_ref: "overview",
                  value_path: "value",
                },
              },
            ],
          },
        ],
      },
      {
        id: "page-drivers",
        title: "Drivers",
        layout: {},
        sections: [
          {
            id: "section-drivers",
            title: "Drivers Section",
            layout: {},
            widgets: [
              {
                id: "widget-drivers-chart",
                kind: "chart",
                title: "Driver Breakdown",
                presentation: {
                  family: "bar",
                  variant: "auto",
                  config: { metric: "contribution" },
                },
                binding: {
                  source_ref: "drivers",
                  value_path: "rows",
                },
              },
            ],
          },
        ],
      },
      {
        id: "page-actions",
        title: "Actions",
        layout: {},
        sections: [
          {
            id: "section-actions",
            title: "Actions Section",
            layout: {},
            widgets: [
              {
                id: "widget-actions-text",
                kind: "text",
                title: "Action Plan",
                presentation: {
                  family: "text",
                  variant: "note",
                  config: {},
                },
                binding: {
                  source_ref: "actions",
                  value_path: "text",
                },
              },
            ],
          },
        ],
      },
    ],
  },
};

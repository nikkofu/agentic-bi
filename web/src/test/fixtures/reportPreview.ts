import type { ReportPreviewPayload } from "../../types/reporting";

export const reportPreviewFixture: ReportPreviewPayload = {
  dashboard: {
    id: "dash-preview-fixture-1",
    version: "1.0",
    title: "上个月华东区毛利率是多少？",
    description: "Auto-generated dashboard preview",
    theme: {},
    refresh_policy: {},
    variables: [],
    data_bindings: [
      {
        id: "binding-fixture-1",
        kind: "materialized_result",
        source_ref: "sq-fixture-1",
        query_id: "sq-fixture-1",
        value: 0.32,
        rows: [
          { month: "2025-12", value: 0.28, gross_margin_rate: 0.28 },
          { month: "2026-01", value: 0.3, gross_margin_rate: 0.3 },
          { month: "2026-02", value: 0.32, gross_margin_rate: 0.32 }
        ],
        insight: "华东区毛利率持续改善，最近一个月达到 32%。",
        text: "本报表由自动化分析生成。"
      }
    ],
    interactions: [],
    pages: [
      {
        id: "page-1",
        title: "Overview",
        layout: {},
        sections: [
          {
            id: "section-1",
            title: "概览",
            layout: {},
            widgets: [
              {
                id: "widget-metric-1",
                kind: "metric_card",
                title: "核心指标",
                presentation: {
                  family: "kpi",
                  variant: "primary",
                  config: {
                    metric: "gross_margin_rate"
                  }
                },
                binding: {
                  source_ref: "sq-fixture-1",
                  value_path: "value"
                }
              },
              {
                id: "widget-chart-1",
                kind: "chart",
                title: "趋势/分布",
                presentation: {
                  family: "line",
                  variant: "auto",
                  config: {
                    metric: "gross_margin_rate"
                  }
                },
                binding: {
                  source_ref: "sq-fixture-1",
                  value_path: "rows"
                }
              },
              {
                id: "widget-insight-1",
                kind: "insight",
                title: "分析说明",
                presentation: {
                  family: "text",
                  variant: "paragraph",
                  title: "分析说明",
                  config: {}
                },
                binding: {
                  source_ref: "sq-fixture-1",
                  value_path: "$.narrative"
                }
              },
              {
                id: "widget-text-1",
                kind: "text",
                title: "备注",
                presentation: {
                  family: "text",
                  variant: "note",
                  config: {}
                },
                binding: {
                  source_ref: "sq-fixture-1",
                  value_path: "text"
                }
              }
            ]
          }
        ]
      }
    ]
  }
};

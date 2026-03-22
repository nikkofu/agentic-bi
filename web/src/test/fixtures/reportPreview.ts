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
        kind: "materialized_result",
        source_ref: "sq-fixture-1",
        query_id: "sq-fixture-1"
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
                  config: {}
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
                  family: "table_like",
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
              }
            ]
          }
        ]
      }
    ]
  }
};

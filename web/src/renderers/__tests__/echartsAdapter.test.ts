import { buildEChartsOption, getRowsForWidget } from "../echartsAdapter";
import { reportPreviewFixture } from "../../test/fixtures/reportPreview";

it("maps line-family chart presentations to an ECharts option", () => {
  const dashboard = reportPreviewFixture.dashboard;
  const chartWidget = dashboard.pages[0].sections[0].widgets.find((widget) => widget.kind === "chart")!;
  const rows = getRowsForWidget(chartWidget, dashboard.data_bindings);
  const option = buildEChartsOption(chartWidget.presentation, rows);

  expect(option.xAxis.type).toBe("category");
  expect(option.series[0].type).toBe("line");
});

it("falls back to a bar-series option for non-line chart families", () => {
  const option = buildEChartsOption(
    {
      family: "bar",
      variant: "auto",
      title: null,
      config: { metric: "gross_margin_rate" },
    },
    [
      { region: "华东", value: 0.32 },
      { region: "华南", value: 0.27 },
    ],
  );

  expect(option.xAxis.type).toBe("category");
  expect(option.series[0].type).toBe("bar");
});

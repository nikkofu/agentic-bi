import { render, screen } from "@testing-library/react";
import { getRowsForWidget, buildEChartsOption } from "../../renderers/echartsAdapter";
import { DashboardPage } from "../DashboardPage";
import { reportPreviewFixture } from "../../test/fixtures/reportPreview";

it("renders dashboard title and top-level widgets", () => {
  render(<DashboardPage dashboard={reportPreviewFixture.dashboard} />);
  expect(screen.getByText("上个月华东区毛利率是多少？")).toBeInTheDocument();
  expect(screen.getByText("核心指标")).toBeInTheDocument();
  expect(screen.getByText("趋势/分布")).toBeInTheDocument();
  expect(screen.getByText("分析说明")).toBeInTheDocument();
  expect(screen.getByText("备注")).toBeInTheDocument();
});

it("omits empty page headings and falls back to presentation title", () => {
  const dashboard = {
    ...reportPreviewFixture.dashboard,
    pages: [
      {
        ...reportPreviewFixture.dashboard.pages[0],
        title: null,
        sections: [
          {
            ...reportPreviewFixture.dashboard.pages[0].sections[0],
            widgets: [
              {
                ...reportPreviewFixture.dashboard.pages[0].sections[0].widgets[0],
                title: null,
                presentation: {
                  ...reportPreviewFixture.dashboard.pages[0].sections[0].widgets[0].presentation,
                  title: "Fallback Widget Title",
                },
              },
            ],
          },
        ],
      },
    ],
  };

  const { container } = render(<DashboardPage dashboard={dashboard} />);

  expect(container.querySelector("h2")).toBeNull();
  expect(screen.getByText("Fallback Widget Title")).toBeInTheDocument();
});

it("renders chart widgets from bound rows", () => {
  render(<DashboardPage dashboard={reportPreviewFixture.dashboard} />);
  const chartWidget = reportPreviewFixture.dashboard.pages[0].sections[0].widgets.find(
    (widget) => widget.kind === "chart",
  )!;
  const rows = getRowsForWidget(chartWidget, reportPreviewFixture.dashboard.data_bindings);
  const option = buildEChartsOption(chartWidget.presentation, rows);

  expect(option.xAxis.type).toBe("category");
  expect(screen.getByTestId("chart-widget")).toBeInTheDocument();
});

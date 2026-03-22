import { BarChart, LineChart } from "echarts/charts";
import { DatasetComponent, GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import ReactEChartsCore from "echarts-for-react/lib/core";

import type { DataBinding, DashboardWidget } from "../types/reporting";
import { buildEChartsOption, getRowsForWidget } from "../renderers/echartsAdapter";

echarts.use([BarChart, DatasetComponent, GridComponent, LineChart, SVGRenderer, TooltipComponent]);

export function ChartWidget({
  widget,
  bindings,
}: {
  widget: DashboardWidget;
  bindings: DataBinding[];
}) {
  const rows = getRowsForWidget(widget, bindings);
  const option = buildEChartsOption(widget.presentation, rows);

  return (
    <article className="widget-card widget-card--chart">
      <h3>{widget.title ?? widget.presentation.title ?? widget.kind}</h3>
      <ReactEChartsCore
        data-testid="chart-widget"
        echarts={echarts}
        option={option}
        notMerge
        lazyUpdate
        opts={{ renderer: "svg" }}
        style={{ height: 280, width: "100%" }}
      />
    </article>
  );
}

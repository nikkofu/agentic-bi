import type { DataBinding, DashboardWidget } from "../types/reporting";

function findBinding(widget: DashboardWidget, bindings: DataBinding[]): DataBinding | undefined {
  return bindings.find((binding) => binding.source_ref === widget.binding.source_ref);
}

function formatMetricValue(value: DataBinding["value"]): string {
  if (typeof value !== "number") {
    return "N/A";
  }

  if (value >= 0 && value <= 1) {
    return `${(value * 100).toFixed(1)}%`;
  }

  return value.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

export function MetricCardWidget({
  widget,
  bindings,
}: {
  widget: DashboardWidget;
  bindings: DataBinding[];
}) {
  const binding = findBinding(widget, bindings);

  return (
    <article className="widget-card widget-card--metric">
      <h3>{widget.title ?? widget.presentation.title ?? widget.kind}</h3>
      <p className="metric-value">{formatMetricValue(binding?.value)}</p>
    </article>
  );
}

import type { DataBinding, DashboardWidget } from "../types/reporting";

function findBinding(widget: DashboardWidget, bindings: DataBinding[]): DataBinding | undefined {
  return bindings.find((binding) => binding.source_ref === widget.binding.source_ref);
}

export function InsightWidget({
  widget,
  bindings,
}: {
  widget: DashboardWidget;
  bindings: DataBinding[];
}) {
  const binding = findBinding(widget, bindings);
  const insight = binding?.insight ?? "No insight available.";

  return (
    <article className="widget-card widget-card--insight">
      <h3>{widget.title ?? widget.presentation.title ?? widget.kind}</h3>
      <p>{insight}</p>
    </article>
  );
}

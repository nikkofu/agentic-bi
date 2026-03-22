import type { DataBinding, DashboardWidget } from "../types/reporting";

function findBinding(widget: DashboardWidget, bindings: DataBinding[]): DataBinding | undefined {
  return bindings.find((binding) => binding.source_ref === widget.binding.source_ref);
}

export function TextWidget({
  widget,
  bindings,
}: {
  widget: DashboardWidget;
  bindings: DataBinding[];
}) {
  const binding = findBinding(widget, bindings);
  const text = binding?.text ?? widget.presentation.title ?? widget.title ?? widget.kind;

  return (
    <article className="widget-card widget-card--text">
      <h3>{widget.title ?? widget.presentation.title ?? widget.kind}</h3>
      <p>{text}</p>
    </article>
  );
}

import type { DashboardWidget } from "../types/reporting";

export function WidgetRenderer({ widgets }: { widgets: DashboardWidget[] }) {
  return (
    <div className="widget-grid">
      {widgets.map((widget) => (
        <article key={widget.id} className="widget-card">
          <h3>{widget.title ?? widget.presentation.title ?? widget.kind}</h3>
        </article>
      ))}
    </div>
  );
}

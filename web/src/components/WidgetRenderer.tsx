import type { DataBinding, DashboardWidget } from "../types/reporting";
import { ChartWidget } from "./ChartWidget";
import { InsightWidget } from "./InsightWidget";
import { MetricCardWidget } from "./MetricCardWidget";
import { TextWidget } from "./TextWidget";

export function WidgetRenderer({
  widgets,
  bindings,
}: {
  widgets: DashboardWidget[];
  bindings: DataBinding[];
}) {
  return (
    <div className="widget-grid">
      {widgets.map((widget) => {
        if (widget.kind === "metric_card") {
          return <MetricCardWidget key={widget.id} widget={widget} bindings={bindings} />;
        }
        if (widget.kind === "chart") {
          return <ChartWidget key={widget.id} widget={widget} bindings={bindings} />;
        }
        if (widget.kind === "insight") {
          return <InsightWidget key={widget.id} widget={widget} bindings={bindings} />;
        }
        if (widget.kind === "text") {
          return <TextWidget key={widget.id} widget={widget} bindings={bindings} />;
        }

        return (
          <article key={widget.id} className="widget-card">
            <h3>{widget.title ?? widget.presentation.title ?? widget.kind}</h3>
          </article>
        );
      })}
    </div>
  );
}

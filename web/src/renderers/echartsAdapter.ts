import type { DataBinding, DashboardWidget, JsonValue, WidgetPresentation } from "../types/reporting";

export type ChartRow = Record<string, string | number | boolean | null>;

function toChartRow(value: JsonValue): ChartRow | null {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  const entries = Object.entries(value).map(([key, entryValue]) => {
    if (
      typeof entryValue === "string" ||
      typeof entryValue === "number" ||
      typeof entryValue === "boolean" ||
      entryValue === null
    ) {
      return [key, entryValue];
    }

    return [key, null];
  });

  return Object.fromEntries(entries);
}

function findBinding(widget: DashboardWidget, bindings: DataBinding[]): DataBinding | undefined {
  return bindings.find((binding) => binding.source_ref === widget.binding.source_ref);
}

function numericValue(row: ChartRow, metricKey: string | null): number {
  if (typeof row.value === "number") {
    return row.value;
  }
  if (metricKey !== null && typeof row[metricKey] === "number") {
    return row[metricKey];
  }
  return 0;
}

function dimensionValue(row: ChartRow, index: number): string | number {
  for (const key of ["month", "label", "category", "region", "name"]) {
    const value = row[key];
    if (typeof value === "string" || typeof value === "number") {
      return value;
    }
  }

  return index + 1;
}

export function getRowsForWidget(widget: DashboardWidget, bindings: DataBinding[]): ChartRow[] {
  const rows = findBinding(widget, bindings)?.rows ?? [];
  return rows.map((row) => toChartRow(row)).filter((row): row is ChartRow => row !== null);
}

export function buildEChartsOption(presentation: WidgetPresentation, rows: ChartRow[]) {
  const metricKey = typeof presentation.config.metric === "string" ? presentation.config.metric : null;
  const xAxisData = rows.map((row, index) => dimensionValue(row, index));
  const seriesData = rows.map((row) => numericValue(row, metricKey));

  if (presentation.family === "line") {
    return {
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: xAxisData },
      yAxis: { type: "value" },
      series: [{ type: "line", data: seriesData }],
    };
  }

  return {
    dataset: { source: rows },
    xAxis: { type: "category", data: xAxisData },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: seriesData }],
  };
}

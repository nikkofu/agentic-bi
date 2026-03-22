export type JsonValue =
  | string
  | number
  | boolean
  | null
  | { [key: string]: JsonValue }
  | JsonValue[];

export interface WidgetPresentation {
  family: string;
  variant?: string | null;
  title?: string | null;
  config: Record<string, JsonValue>;
}

export interface WidgetBinding {
  source_ref: string;
  query_id?: string | null;
  value_path?: string | null;
}

export interface DashboardWidget {
  id: string;
  kind: string;
  title?: string | null;
  presentation: WidgetPresentation;
  binding: WidgetBinding;
}

export interface DashboardSection {
  id: string;
  title?: string | null;
  layout: Record<string, JsonValue>;
  widgets: DashboardWidget[];
}

export interface DashboardPageSpec {
  id: string;
  title?: string | null;
  layout: Record<string, JsonValue>;
  sections: DashboardSection[];
}

export interface DataBinding {
  id?: string;
  source_ref: string;
  kind: string;
  query_id?: string | null;
  value?: JsonValue;
  rows?: JsonValue[];
  insight?: string;
  text?: string;
}

export interface DashboardSpec {
  id: string;
  version: string;
  title: string;
  description?: string | null;
  theme: Record<string, JsonValue>;
  refresh_policy: Record<string, JsonValue>;
  variables: Record<string, JsonValue>[];
  data_bindings: DataBinding[];
  interactions: Record<string, JsonValue>[];
  pages: DashboardPageSpec[];
}

export interface ReportPreviewPayload {
  dashboard: DashboardSpec;
}

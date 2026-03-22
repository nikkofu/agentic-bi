import type { DashboardDocument, DiagnosticReportDocument, ReportIntent, ReportPreviewPayload } from "../types/reporting";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const DEFAULT_VIEWER_CONTEXT = {
  tenant_id: "t-1",
  user_id: "u-1",
  principal_id: "u-1",
};
export type ViewerContext = typeof DEFAULT_VIEWER_CONTEXT;

export function resolveViewerContext(overrides?: Partial<ViewerContext>): ViewerContext {
  return {
    tenant_id: overrides?.tenant_id ?? DEFAULT_VIEWER_CONTEXT.tenant_id,
    user_id: overrides?.user_id ?? DEFAULT_VIEWER_CONTEXT.user_id,
    principal_id: overrides?.principal_id ?? DEFAULT_VIEWER_CONTEXT.principal_id,
  };
}

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  const body = (await response.json().catch(() => null)) as T | { detail?: { error_code?: string } } | null;

  if (!response.ok) {
    const errorCode =
      body !== null &&
      typeof body === "object" &&
      "detail" in body &&
      body.detail !== undefined &&
      typeof body.detail === "object" &&
      body.detail !== null &&
      "error_code" in body.detail &&
      typeof body.detail.error_code === "string"
        ? body.detail.error_code
        : `HTTP_${response.status}`;
    throw new Error(errorCode);
  }

  return body as T;
}

export async function fetchPreview(question: string): Promise<ReportPreviewPayload> {
  const intent = await fetchJson<ReportIntent>(`${API_BASE_URL}/v1/report-intents:generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...DEFAULT_VIEWER_CONTEXT,
      conversation_id: "preview-session",
      question,
    }),
  });

  return fetchJson<ReportPreviewPayload>(`${API_BASE_URL}/v1/dashboards:assemble`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...DEFAULT_VIEWER_CONTEXT,
      intent,
    }),
  });
}

export async function fetchDashboardForViewer(
  dashboardId: string,
  viewerContext: ViewerContext = DEFAULT_VIEWER_CONTEXT,
): Promise<DashboardDocument> {
  const params = new URLSearchParams(viewerContext);
  return fetchJson<DashboardDocument>(`${API_BASE_URL}/v1/dashboards/${dashboardId}?${params.toString()}`);
}

export async function fetchReport(
  reportId: string,
  viewerContext: ViewerContext = DEFAULT_VIEWER_CONTEXT,
): Promise<DiagnosticReportDocument> {
  const params = new URLSearchParams(viewerContext);
  return fetchJson<DiagnosticReportDocument>(`${API_BASE_URL}/v1/reports/${reportId}?${params.toString()}`);
}

export async function fetchDashboard(dashboardId: string): Promise<DashboardDocument> {
  return fetchDashboardForViewer(dashboardId, DEFAULT_VIEWER_CONTEXT);
}

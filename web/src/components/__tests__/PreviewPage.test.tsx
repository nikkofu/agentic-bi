import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../../App";
import { reportPreviewFixture } from "../../test/fixtures/reportPreview";

const originalFetch = global.fetch;
const previewIntent = {
  id: "ri-preview-1",
  version: "1.0",
  tenant_id: "t-1",
  dataset_id: "sales-fixture",
  source: "chat",
  question: "上个月华东区毛利率是多少？",
  goal: "answer question",
  permission_context: {
    principal_id: "u-1",
    role_scope: ["region:华东"],
    row_level_policy_ref: "sales-region:u-1",
  },
  semantic_queries: [
    {
      id: "sq-fixture-1",
      kind: "metric",
      measures: ["gross_margin_rate"],
      dimensions: [],
      filters: [{ field: "region", op: "=", value: "华东" }],
      time: { window: "last_month" },
      display_hint: {},
    },
  ],
  explanations: [],
  constraints: {},
  trace: { trace_id: "trace-preview-1" },
};

function mockJsonResponse(body: unknown): Promise<Response> {
  return Promise.resolve({
    ok: true,
    json: async () => body,
  } as Response);
}

afterEach(() => {
  vi.restoreAllMocks();
  global.fetch = originalFetch;
});

it("loads a preview dashboard from the backend", async () => {
  global.fetch = vi
    .fn()
    .mockImplementationOnce(() => mockJsonResponse(previewIntent))
    .mockImplementationOnce(() => mockJsonResponse(reportPreviewFixture));

  render(
    <MemoryRouter initialEntries={["/preview?question=上个月华东区毛利率是多少？"]}>
      <App />
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByText("Auto Reporting Preview")).toBeInTheDocument());
  expect(screen.getByText("上个月华东区毛利率是多少？")).toBeInTheDocument();
});

it("loads a saved dashboard from the backend", async () => {
  global.fetch = vi.fn().mockImplementationOnce(() =>
    mockJsonResponse({
      dashboard_id: reportPreviewFixture.dashboard.id,
      report_intent_id: "ri-preview-1",
      current_revision_id: "rev-1",
      published_revision_id: "rev-1",
      dashboard: reportPreviewFixture.dashboard,
      report_intent: previewIntent,
    }),
  );

  render(
    <MemoryRouter initialEntries={[`/dashboards/${reportPreviewFixture.dashboard.id}`]}>
      <App />
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByText("Auto Reporting Preview")).toBeInTheDocument());
  expect(screen.getByText("核心指标")).toBeInTheDocument();
});

import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../../App";
import { diagnosticReportFixture } from "../../test/fixtures/diagnosticReport";

const originalFetch = global.fetch;

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

it("loads a diagnostic report from the canonical report route", async () => {
  global.fetch = vi.fn().mockImplementationOnce(() => mockJsonResponse(diagnosticReportFixture));

  render(
    <MemoryRouter initialEntries={["/reports/dr-1"]}>
      <App />
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByText("Diagnostic Report")).toBeInTheDocument());
  expect(screen.getByText(diagnosticReportFixture.report.summary.title)).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "Drivers" })).toBeInTheDocument();
});

it("passes viewer identity from report route query params", async () => {
  const fetchMock = vi.fn().mockImplementationOnce(() => mockJsonResponse(diagnosticReportFixture));
  global.fetch = fetchMock;

  render(
    <MemoryRouter initialEntries={["/reports/dr-1?tenant_id=t-1&user_id=u-south&principal_id=u-south"]}>
      <App />
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByText("Diagnostic Report")).toBeInTheDocument());
  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining("/v1/reports/dr-1?tenant_id=t-1&user_id=u-south&principal_id=u-south"),
    undefined,
  );
});

it("fills a missing principal_id from the report route user_id", async () => {
  const fetchMock = vi.fn().mockImplementationOnce(() => mockJsonResponse(diagnosticReportFixture));
  global.fetch = fetchMock;

  render(
    <MemoryRouter initialEntries={["/reports/dr-1?tenant_id=t-1&user_id=u-south"]}>
      <App />
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByText("Diagnostic Report")).toBeInTheDocument());
  expect(fetchMock).toHaveBeenCalledWith(
    expect.stringContaining("/v1/reports/dr-1?tenant_id=t-1&user_id=u-south&principal_id=u-south"),
    undefined,
  );
});

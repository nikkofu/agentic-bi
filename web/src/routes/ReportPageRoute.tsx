import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { fetchReport, resolveViewerContext } from "../api/client";
import { DashboardPage } from "../components/DashboardPage";
import type { DiagnosticReportDocument } from "../types/reporting";

function RouteStatus({
  eyebrow,
  title,
  message,
}: {
  eyebrow: string;
  title: string;
  message: string;
}) {
  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <p className="dashboard-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="dashboard-empty-state">{message}</p>
      </header>
    </main>
  );
}

export function ReportPageRoute() {
  const { reportId = "" } = useParams();
  const [searchParams] = useSearchParams();
  const [document, setDocument] = useState<DiagnosticReportDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const tenantId = searchParams.get("tenant_id") ?? undefined;
  const userId = searchParams.get("user_id") ?? undefined;
  const principalId = searchParams.get("principal_id") ?? undefined;

  useEffect(() => {
    let isActive = true;
    const viewerContext = resolveViewerContext({
      tenant_id: tenantId,
      user_id: userId,
      principal_id: principalId,
    });

    if (reportId.length === 0) {
      setDocument(null);
      setError("Provide a report id in the route path.");
      setIsLoading(false);
      return () => {
        isActive = false;
      };
    }

    setIsLoading(true);
    setError(null);

    void fetchReport(reportId, viewerContext)
      .then((payload) => {
        if (!isActive) {
          return;
        }
        setDocument(payload);
        setIsLoading(false);
      })
      .catch((caughtError: unknown) => {
        if (!isActive) {
          return;
        }
        setDocument(null);
        setError(caughtError instanceof Error ? caughtError.message : "Failed to load report.");
        setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [principalId, reportId, tenantId, userId]);

  if (isLoading) {
    return (
      <RouteStatus
        eyebrow="Loading Report"
        title="Loading diagnostic report"
        message="The viewer is fetching the latest saved diagnostic report."
      />
    );
  }

  if (error !== null) {
    return <RouteStatus eyebrow="Report Error" title="Report unavailable" message={error} />;
  }

  if (document === null) {
    return <RouteStatus eyebrow="Diagnostic Report" title="No report available" message="No saved diagnostic report payload returned." />;
  }

  return (
    <DashboardPage
      dashboard={document.dashboard}
      eyebrow="Diagnostic Report"
      title={document.report.summary.title}
    />
  );
}

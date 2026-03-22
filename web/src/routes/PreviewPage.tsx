import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchPreview } from "../api/client";
import { DashboardPage } from "../components/DashboardPage";
import type { DashboardSpec } from "../types/reporting";

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

export function PreviewPage() {
  const [searchParams] = useSearchParams();
  const question = searchParams.get("question")?.trim() ?? "";
  const [dashboard, setDashboard] = useState<DashboardSpec | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    if (question.length === 0) {
      setDashboard(null);
      setError("Provide a question in the preview query string.");
      setIsLoading(false);
      return () => {
        isActive = false;
      };
    }

    setIsLoading(true);
    setError(null);

    void fetchPreview(question)
      .then((payload) => {
        if (!isActive) {
          return;
        }
        setDashboard(payload.dashboard);
        setIsLoading(false);
      })
      .catch((caughtError: unknown) => {
        if (!isActive) {
          return;
        }
        setDashboard(null);
        setError(caughtError instanceof Error ? caughtError.message : "Failed to load preview dashboard.");
        setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [question]);

  if (isLoading) {
    return (
      <RouteStatus
        eyebrow="Loading Preview"
        title="Generating dashboard preview"
        message="The viewer is requesting a report intent and assembling the dashboard."
      />
    );
  }

  if (error !== null) {
    return <RouteStatus eyebrow="Preview Error" title="Preview unavailable" message={error} />;
  }

  if (dashboard === null) {
    return <RouteStatus eyebrow="Preview Ready" title="No preview available" message="No dashboard payload returned." />;
  }

  return <DashboardPage dashboard={dashboard} />;
}

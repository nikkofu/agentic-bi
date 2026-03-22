import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchDashboard } from "../api/client";
import { DashboardPage } from "../components/DashboardPage";
import type { DashboardDocument } from "../types/reporting";

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

export function DashboardPageRoute() {
  const { dashboardId = "" } = useParams();
  const [document, setDocument] = useState<DashboardDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isActive = true;

    if (dashboardId.length === 0) {
      setDocument(null);
      setError("Provide a dashboard id in the route path.");
      setIsLoading(false);
      return () => {
        isActive = false;
      };
    }

    setIsLoading(true);
    setError(null);

    void fetchDashboard(dashboardId)
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
        setError(caughtError instanceof Error ? caughtError.message : "Failed to load dashboard.");
        setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [dashboardId]);

  if (isLoading) {
    return (
      <RouteStatus
        eyebrow="Loading Dashboard"
        title="Loading saved dashboard"
        message="The viewer is fetching the latest persisted dashboard revision."
      />
    );
  }

  if (error !== null) {
    return <RouteStatus eyebrow="Dashboard Error" title="Dashboard unavailable" message={error} />;
  }

  if (document === null) {
    return <RouteStatus eyebrow="Dashboard Ready" title="No dashboard available" message="No saved dashboard payload returned." />;
  }

  return <DashboardPage dashboard={document.dashboard} />;
}

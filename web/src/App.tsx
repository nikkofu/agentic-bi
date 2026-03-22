import type { DashboardSpec } from "./types/reporting";
import { DashboardPage } from "./components/DashboardPage";

export function App({ dashboard = null }: { dashboard?: DashboardSpec | null }) {
  if (dashboard === null) {
    return (
      <main className="dashboard-shell">
        <header className="dashboard-header">
          <p className="dashboard-eyebrow">Auto Reporting Preview</p>
          <h1>Viewer Scaffold Ready</h1>
          <p className="dashboard-empty-state">
            Dashboard data wiring lands in Task 7. This shell is ready to render a preview or saved dashboard.
          </p>
        </header>
      </main>
    );
  }

  return <DashboardPage dashboard={dashboard} />;
}

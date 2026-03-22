import { Route, Routes } from "react-router-dom";
import { DashboardPage } from "./components/DashboardPage";
import { DashboardPageRoute } from "./routes/DashboardPageRoute";
import { PreviewPage } from "./routes/PreviewPage";
import type { DashboardSpec } from "./types/reporting";

function ViewerScaffold() {
  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <p className="dashboard-eyebrow">Auto Reporting Preview</p>
        <h1>Viewer Ready</h1>
        <p className="dashboard-empty-state">
          Open <code>/preview?question=...</code> to generate a dashboard preview, or <code>/dashboards/:dashboardId</code>
          to view a saved dashboard revision.
        </p>
      </header>
    </main>
  );
}

export function App({ dashboard = null }: { dashboard?: DashboardSpec | null }) {
  if (dashboard !== null) {
    return <DashboardPage dashboard={dashboard} />;
  }

  return (
    <Routes>
      <Route path="/" element={<ViewerScaffold />} />
      <Route path="/preview" element={<PreviewPage />} />
      <Route path="/dashboards/:dashboardId" element={<DashboardPageRoute />} />
      <Route path="*" element={<ViewerScaffold />} />
    </Routes>
  );
}

export default App;

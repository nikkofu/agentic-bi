import type { DashboardSpec } from "../types/reporting";
import { WidgetRenderer } from "./WidgetRenderer";

export function DashboardPage({ dashboard }: { dashboard: DashboardSpec }) {
  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <p className="dashboard-eyebrow">Auto Reporting Preview</p>
        <h1>{dashboard.title}</h1>
      </header>

      {dashboard.pages.map((page) => (
        <section key={page.id} className="dashboard-page">
          {page.title ? <h2>{page.title}</h2> : null}
          <WidgetRenderer widgets={page.sections.flatMap((section) => section.widgets)} />
        </section>
      ))}
    </main>
  );
}

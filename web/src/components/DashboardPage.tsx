import { useEffect, useState } from "react";
import type { DashboardSpec } from "../types/reporting";
import { DashboardPageNav } from "./DashboardPageNav";
import { WidgetRenderer } from "./WidgetRenderer";

export function DashboardPage({
  dashboard,
  eyebrow = "Auto Reporting Preview",
  title,
}: {
  dashboard: DashboardSpec;
  eyebrow?: string;
  title?: string;
}) {
  const firstPageId = dashboard.pages[0]?.id ?? "";
  const [activePageId, setActivePageId] = useState(firstPageId);

  useEffect(() => {
    setActivePageId(dashboard.pages[0]?.id ?? "");
  }, [dashboard]);

  const activePage = dashboard.pages.find((page) => page.id === activePageId) ?? dashboard.pages[0] ?? null;

  return (
    <main className="dashboard-shell">
      <header className="dashboard-header">
        <p className="dashboard-eyebrow">{eyebrow}</p>
        <h1>{title ?? dashboard.title}</h1>
      </header>

      <DashboardPageNav pages={dashboard.pages} activePageId={activePage?.id ?? ""} onSelectPage={setActivePageId} />

      {activePage !== null ? (
        <section
          key={activePage.id}
          id={`dashboard-panel-${activePage.id}`}
          className="dashboard-page"
          role="tabpanel"
          aria-labelledby={`dashboard-tab-${activePage.id}`}
        >
          {activePage.title ? <h2>{activePage.title}</h2> : null}
          <WidgetRenderer
            widgets={activePage.sections.flatMap((section) => section.widgets)}
            bindings={dashboard.data_bindings}
          />
        </section>
      ) : null}
    </main>
  );
}

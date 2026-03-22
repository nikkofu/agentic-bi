import type { DashboardPageSpec } from "../types/reporting";

export function DashboardPageNav({
  pages,
  activePageId,
  onSelectPage,
}: {
  pages: DashboardPageSpec[];
  activePageId: string;
  onSelectPage: (pageId: string) => void;
}) {
  if (pages.length <= 1) {
    return null;
  }

  return (
    <nav aria-label="Dashboard pages">
      <div role="tablist" aria-label="Dashboard pages">
        {pages.map((page) => {
          const label = page.title?.trim() || page.id;
          const isActive = page.id === activePageId;

          return (
            <button
              key={page.id}
              id={`dashboard-tab-${page.id}`}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`dashboard-panel-${page.id}`}
              onClick={() => onSelectPage(page.id)}
            >
              {label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

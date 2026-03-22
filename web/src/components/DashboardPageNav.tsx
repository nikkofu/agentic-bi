import { useRef } from "react";
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
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  if (pages.length <= 1) {
    return null;
  }

  function moveToPage(nextIndex: number) {
    const nextPage = pages[nextIndex];
    if (!nextPage) {
      return;
    }

    onSelectPage(nextPage.id);
    tabRefs.current[nextIndex]?.focus();
  }

  return (
    <nav aria-label="Dashboard pages">
      <div role="tablist" aria-label="Dashboard pages">
        {pages.map((page, index) => {
          const label = page.title?.trim() || page.id;
          const isActive = page.id === activePageId;

          return (
            <button
              key={page.id}
              ref={(element) => {
                tabRefs.current[index] = element;
              }}
              id={`dashboard-tab-${page.id}`}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`dashboard-panel-${page.id}`}
              tabIndex={isActive ? 0 : -1}
              onKeyDown={(event) => {
                if (event.key === "ArrowRight") {
                  event.preventDefault();
                  moveToPage((index + 1) % pages.length);
                }

                if (event.key === "ArrowLeft") {
                  event.preventDefault();
                  moveToPage((index - 1 + pages.length) % pages.length);
                }
              }}
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

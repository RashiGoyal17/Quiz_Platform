import { useEffect, useState } from "react";

function readStoredCollapsed(storageKey: string): boolean {
  return window.localStorage.getItem(storageKey) === "true";
}

/**
 * Tracks responsive sidebar UI state: a temporary mobile drawer (transient,
 * never persisted) and a desktop collapse toggle (persisted per `storageKey`
 * so the layout preference survives refreshes/restarts).
 */
export function useSidebarState(storageKey: string) {
  const [collapsed, setCollapsed] = useState(() => readStoredCollapsed(storageKey));
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    window.localStorage.setItem(storageKey, String(collapsed));
  }, [storageKey, collapsed]);

  return {
    collapsed,
    toggleCollapsed: () => setCollapsed((prev) => !prev),
    mobileOpen,
    openMobile: () => setMobileOpen(true),
    closeMobile: () => setMobileOpen(false),
  };
}

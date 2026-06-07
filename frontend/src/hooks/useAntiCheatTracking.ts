import { useEffect, useRef } from "react";

import type { TabSwitchResponse } from "../api/types";
import { useLogProctoringEventMutation, useLogTabSwitchMutation } from "./useAttempts";

interface UseAntiCheatTrackingOptions {
  attemptId: string;
  active: boolean;
  onTabSwitchLogged?: (result: TabSwitchResponse) => void;
  onWindowBlur?: () => void;
  onWindowFocus?: () => void;
}

/**
 * Wires window blur/focus and tab-visibility changes to the existing
 * anti-cheat endpoints. Tab switches go through the dedicated /tab-switch
 * endpoint (the generic proctoring-event endpoint rejects that type);
 * window blur is logged as a "window_blur" proctoring event. Window focus
 * has no backend event type, so it is surfaced only via `onFocusChange`
 * for client-side UI feedback.
 */
export function useAntiCheatTracking({
  attemptId,
  active,
  onTabSwitchLogged,
  onWindowBlur,
  onWindowFocus,
}: UseAntiCheatTrackingOptions) {
  const tabSwitchMutation = useLogTabSwitchMutation(attemptId);
  const proctoringEventMutation = useLogProctoringEventMutation(attemptId);

  const tabSwitchMutateRef = useRef(tabSwitchMutation.mutate);
  const proctoringEventMutateRef = useRef(proctoringEventMutation.mutate);
  const onTabSwitchLoggedRef = useRef(onTabSwitchLogged);
  const onWindowBlurRef = useRef(onWindowBlur);
  const onWindowFocusRef = useRef(onWindowFocus);

  useEffect(() => {
    tabSwitchMutateRef.current = tabSwitchMutation.mutate;
    proctoringEventMutateRef.current = proctoringEventMutation.mutate;
    onTabSwitchLoggedRef.current = onTabSwitchLogged;
    onWindowBlurRef.current = onWindowBlur;
    onWindowFocusRef.current = onWindowFocus;
  });

  useEffect(() => {
    if (!active) return;

    const handleBlur = () => {
      onWindowBlurRef.current?.();
      proctoringEventMutateRef.current({ event_type: "window_blur" });
    };

    const handleFocus = () => {
      // No backend "window_focus" event type exists — surfaced client-side only.
      onWindowFocusRef.current?.();
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        tabSwitchMutateRef.current(undefined, {
          onSuccess: (result) => onTabSwitchLoggedRef.current?.(result),
        });
      }
    };

    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [active]);
}

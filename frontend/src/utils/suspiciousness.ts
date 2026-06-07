import type { ChipProps } from "@mui/material";

import type { ProctoringEventResponse } from "../api/types";

export type SuspiciousnessLevel = "Low" | "Medium" | "High";

const LEVELS: SuspiciousnessLevel[] = ["Low", "Medium", "High"];

export const SUSPICIOUSNESS_COLORS: Record<SuspiciousnessLevel, ChipProps["color"]> = {
  Low: "success",
  Medium: "warning",
  High: "error",
};

/**
 * Frontend-only heuristic: base level from tab-switch volume, escalated by
 * one level for each higher-risk signal present (copy/paste, fullscreen exit),
 * capped at High. Not a backend-verified score — a quick triage signal only.
 */
export function calculateSuspiciousness(
  tabSwitchCount: number,
  proctoringEvents: Pick<ProctoringEventResponse, "event_type">[],
): SuspiciousnessLevel {
  let levelIndex = tabSwitchCount > 5 ? 2 : tabSwitchCount >= 3 ? 1 : 0;

  const eventTypes = new Set(proctoringEvents.map((event) => event.event_type));
  if (eventTypes.has("copy_paste")) levelIndex = Math.min(levelIndex + 1, LEVELS.length - 1);
  if (eventTypes.has("fullscreen_exit")) levelIndex = Math.min(levelIndex + 1, LEVELS.length - 1);

  return LEVELS[levelIndex];
}

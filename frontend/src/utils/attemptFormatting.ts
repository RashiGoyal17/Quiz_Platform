import type { ChipProps } from "@mui/material";

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

const scoreFormatter = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatScore(value: number | null): string {
  return value === null ? "—" : scoreFormatter.format(value);
}

export function formatDateTime(value: string | null): string {
  return value ? dateTimeFormatter.format(new Date(value)) : "—";
}

export const STATUS_COLORS: Record<string, ChipProps["color"]> = {
  submitted: "success",
  in_progress: "info",
  timed_out: "warning",
  abandoned: "error",
};

/**
 * Shortens a UUID for display (e.g. in tables) where the full value would be
 * too wide to show. Pair with a Tooltip showing the full id for reference.
 */
export function shortenId(id: string, length = 8): string {
  return id.length > length ? `${id.slice(0, length)}…` : id;
}

export function statusLabel(status: string): string {
  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

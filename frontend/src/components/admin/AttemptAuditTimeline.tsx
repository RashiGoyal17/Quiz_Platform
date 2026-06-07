import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ContentPasteIcon from "@mui/icons-material/ContentPaste";
import FlagIcon from "@mui/icons-material/Flag";
import FullscreenExitIcon from "@mui/icons-material/FullscreenExit";
import SwapHorizIcon from "@mui/icons-material/SwapHoriz";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { Box, List, ListItem, ListItemIcon, ListItemText, Typography } from "@mui/material";
import type { ReactNode } from "react";

import type { AttemptAdminItem, ProctoringEventResponse, TabSwitchLog } from "../../api/types";
import { statusLabel } from "../../utils/attemptFormatting";

const timeFormatter = new Intl.DateTimeFormat(undefined, { timeStyle: "short" });

function formatTime(value: string): string {
  return timeFormatter.format(new Date(value));
}

const EVENT_LABELS: Record<string, string> = {
  tab_switch: "Tab Switch",
  window_blur: "Window Blur",
  copy_paste: "Copy Paste",
  fullscreen_exit: "Fullscreen Exit",
  face_not_detected: "Face Not Detected",
  multiple_faces: "Multiple Faces",
  phone_detected: "Phone Detected",
  audio_detected: "Audio Detected",
};

const EVENT_ICONS: Record<string, ReactNode> = {
  tab_switch: <SwapHorizIcon fontSize="small" />,
  window_blur: <VisibilityOffIcon fontSize="small" />,
  copy_paste: <ContentPasteIcon fontSize="small" />,
  fullscreen_exit: <FullscreenExitIcon fontSize="small" />,
};

const FINAL_LABELS: Record<string, string> = {
  submitted: "Submit",
  timed_out: "Timed Out",
  abandoned: "Abandoned",
};

interface TimelineEntry {
  id: string;
  time: string;
  label: string;
  icon: ReactNode;
}

interface AttemptAuditTimelineProps {
  attempt: AttemptAdminItem;
  tabSwitchLogs: TabSwitchLog[];
  proctoringEvents: ProctoringEventResponse[];
}

export function AttemptAuditTimeline({
  attempt,
  tabSwitchLogs,
  proctoringEvents,
}: AttemptAuditTimelineProps) {
  const entries: TimelineEntry[] = [
    {
      id: "start",
      time: attempt.started_at,
      label: "Start Attempt",
      icon: <FlagIcon fontSize="small" />,
    },
    ...tabSwitchLogs.map((log) => ({
      id: `tab-switch-${log.id}`,
      time: log.switched_at,
      label: EVENT_LABELS.tab_switch,
      icon: EVENT_ICONS.tab_switch,
    })),
    ...proctoringEvents.map((event) => ({
      id: `proctoring-${event.id}`,
      time: event.occurred_at,
      label: EVENT_LABELS[event.event_type] ?? statusLabel(event.event_type),
      icon: EVENT_ICONS[event.event_type] ?? <WarningAmberIcon fontSize="small" />,
    })),
  ];

  if (attempt.submitted_at) {
    entries.push({
      id: "end",
      time: attempt.submitted_at,
      label: FINAL_LABELS[attempt.status] ?? statusLabel(attempt.status),
      icon: <CheckCircleIcon fontSize="small" />,
    });
  }

  entries.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

  if (entries.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No timeline events recorded.
      </Typography>
    );
  }

  return (
    <List disablePadding>
      {entries.map((entry, index) => (
        <ListItem key={entry.id} divider={index < entries.length - 1} sx={{ py: 1 }}>
          <ListItemIcon sx={{ minWidth: 40 }}>{entry.icon}</ListItemIcon>
          <ListItemText
            primary={
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                <Typography variant="body2" sx={{ minWidth: 64, fontWeight: 600 }}>
                  {formatTime(entry.time)}
                </Typography>
                <Typography variant="body2">{entry.label}</Typography>
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  );
}

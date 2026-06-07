import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import { Chip, CircularProgress } from "@mui/material";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

interface SaveStatusIndicatorProps {
  status: SaveStatus;
}

export function SaveStatusIndicator({ status }: SaveStatusIndicatorProps) {
  if (status === "saving") {
    return (
      <Chip
        size="small"
        variant="outlined"
        icon={<CircularProgress size={14} />}
        label="Saving..."
      />
    );
  }

  if (status === "saved") {
    return (
      <Chip
        size="small"
        variant="outlined"
        color="success"
        icon={<CheckCircleIcon />}
        label="Saved"
      />
    );
  }

  if (status === "error") {
    return (
      <Chip size="small" variant="outlined" color="error" icon={<ErrorIcon />} label="Save failed" />
    );
  }

  return null;
}

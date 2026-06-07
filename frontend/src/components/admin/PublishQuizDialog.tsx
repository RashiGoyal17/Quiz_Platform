import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";
import { isAxiosError } from "axios";

import type { ApiErrorResponse, Quiz } from "../../api/types";

export type PublishQuizMode = "publish" | "unpublish";

interface PublishQuizDialogProps {
  open: boolean;
  mode: PublishQuizMode;
  quiz: Quiz | null;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onConfirm: () => void;
}

export function PublishQuizDialog({
  open,
  mode,
  quiz,
  submitting,
  error,
  onClose,
  onConfirm,
}: PublishQuizDialogProps) {
  const errorMessage = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  const isPublish = mode === "publish";
  const title = isPublish ? "Publish quiz" : "Unpublish quiz";
  const actionLabel = isPublish ? "Publish" : "Unpublish";
  const pendingLabel = isPublish ? "Publishing..." : "Unpublishing...";
  const fallbackError = isPublish
    ? "Unable to publish this quiz. Please try again."
    : "Unable to unpublish this quiz. Please try again.";

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {error !== null && error !== undefined && (
          <Alert severity="error">{errorMessage ?? fallbackError}</Alert>
        )}
        <DialogContentText>
          {isPublish ? (
            <>
              Publish <strong>"{quiz?.title}"</strong>? Students will be able to see and
              attempt it once it is published.
            </>
          ) : (
            <>
              Unpublish <strong>"{quiz?.title}"</strong>? Students will no longer be able to
              start new attempts.
            </>
          )}
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color={isPublish ? "primary" : "warning"}
          disabled={submitting}
        >
          {submitting ? pendingLabel : actionLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

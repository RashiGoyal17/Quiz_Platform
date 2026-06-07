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

import type { ApiErrorResponse, Question } from "../../api/types";

interface DeleteQuestionDialogProps {
  open: boolean;
  question: Question | null;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onConfirm: () => void;
}

const PREVIEW_LENGTH = 120;

function previewText(text: string): string {
  return text.length > PREVIEW_LENGTH ? `${text.slice(0, PREVIEW_LENGTH)}…` : text;
}

export function DeleteQuestionDialog({
  open,
  question,
  submitting,
  error,
  onClose,
  onConfirm,
}: DeleteQuestionDialogProps) {
  const errorMessage = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Delete question</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {error !== null && error !== undefined && (
          <Alert severity="error">
            {errorMessage ?? "Unable to delete this question. Please try again."}
          </Alert>
        )}
        <DialogContentText>
          Delete <strong>"{question ? previewText(question.text) : ""}"</strong>? This cannot
          be undone.
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button onClick={onConfirm} variant="contained" color="error" disabled={submitting}>
          {submitting ? "Deleting..." : "Delete"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

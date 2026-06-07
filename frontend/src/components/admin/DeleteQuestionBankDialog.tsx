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

import type { ApiErrorResponse, QuestionBank } from "../../api/types";

interface DeleteQuestionBankDialogProps {
  open: boolean;
  bank: QuestionBank | null;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onConfirm: () => void;
}

export function DeleteQuestionBankDialog({
  open,
  bank,
  submitting,
  error,
  onClose,
  onConfirm,
}: DeleteQuestionBankDialogProps) {
  const errorMessage = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Delete question bank</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {error !== null && error !== undefined && (
          <Alert severity="error">
            {errorMessage ?? "Unable to delete this question bank. Please try again."}
          </Alert>
        )}
        <DialogContentText>
          Delete <strong>{bank?.name}</strong>? This cannot be undone.
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

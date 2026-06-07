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

import type { ApiErrorResponse, QuizQuestion } from "../../api/types";

interface RemoveQuizQuestionDialogProps {
  open: boolean;
  quizQuestion: QuizQuestion | null;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onConfirm: () => void;
}

const PREVIEW_LENGTH = 120;

function previewText(text: string): string {
  return text.length > PREVIEW_LENGTH ? `${text.slice(0, PREVIEW_LENGTH)}…` : text;
}

export function RemoveQuizQuestionDialog({
  open,
  quizQuestion,
  submitting,
  error,
  onClose,
  onConfirm,
}: RemoveQuizQuestionDialogProps) {
  const errorMessage = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Remove question from quiz</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {error !== null && error !== undefined && (
          <Alert severity="error">
            {errorMessage ?? "Unable to remove this question. Please try again."}
          </Alert>
        )}
        <DialogContentText>
          Remove{" "}
          <strong>"{quizQuestion ? previewText(quizQuestion.question.text) : ""}"</strong>{" "}
          from this quiz? Its position and marks override will be lost.
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button onClick={onConfirm} variant="contained" color="error" disabled={submitting}>
          {submitting ? "Removing..." : "Remove"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

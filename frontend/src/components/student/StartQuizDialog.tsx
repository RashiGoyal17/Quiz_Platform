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
import { useNavigate } from "react-router-dom";

import type { ApiErrorResponse, QuizAvailable } from "../../api/types";
import { ROUTES } from "../../constants/routes";
import { useStartAttemptMutation } from "../../hooks/useAttempts";

interface StartQuizDialogProps {
  open: boolean;
  quiz: QuizAvailable | null;
  onClose: () => void;
}

export function StartQuizDialog({ open, quiz, onClose }: StartQuizDialogProps) {
  const navigate = useNavigate();
  const startMutation = useStartAttemptMutation();

  const handleClose = () => {
    startMutation.reset();
    onClose();
  };

  const handleConfirm = () => {
    if (!quiz) return;
    startMutation.mutate(
      { quiz_id: quiz.id },
      {
        onSuccess: (attempt) => {
          startMutation.reset();
          onClose();
          navigate(ROUTES.student.attemptDetail(attempt.id, attempt.quiz_id));
        },
      },
    );
  };

  const errorMessage = isAxiosError<ApiErrorResponse>(startMutation.error)
    ? startMutation.error.response?.data?.detail
    : undefined;

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="xs">
      <DialogTitle>Start quiz</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {startMutation.isError && (
          <Alert severity="error">
            {errorMessage ?? "Unable to start this quiz. Please try again."}
          </Alert>
        )}
        <DialogContentText>
          Start <strong>"{quiz?.title}"</strong>? Once started, the timer begins immediately
          and cannot be paused. If you already have an attempt in progress for this quiz, it
          will be resumed.
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} disabled={startMutation.isPending}>
          Cancel
        </Button>
        <Button onClick={handleConfirm} variant="contained" disabled={startMutation.isPending}>
          {startMutation.isPending ? "Starting..." : "Start quiz"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

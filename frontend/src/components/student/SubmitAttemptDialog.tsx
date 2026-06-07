import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";

interface SubmitAttemptDialogProps {
  open: boolean;
  unansweredCount: number;
  isSubmitting: boolean;
  errorMessage?: string | null;
  onConfirm: () => void;
  onClose: () => void;
}

export function SubmitAttemptDialog({
  open,
  unansweredCount,
  isSubmitting,
  errorMessage,
  onConfirm,
  onClose,
}: SubmitAttemptDialogProps) {
  return (
    <Dialog open={open} onClose={isSubmitting ? undefined : onClose} fullWidth maxWidth="xs">
      <DialogTitle>Submit attempt?</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
        {unansweredCount > 0 && (
          <Alert severity="warning">
            You have {unansweredCount} unanswered question{unansweredCount === 1 ? "" : "s"}.
          </Alert>
        )}
        <DialogContentText>
          Once submitted, your attempt will be graded and you won't be able to change any
          answers. Are you sure you want to submit?
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button onClick={onConfirm} variant="contained" disabled={isSubmitting}>
          {isSubmitting ? "Submitting..." : "Submit attempt"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

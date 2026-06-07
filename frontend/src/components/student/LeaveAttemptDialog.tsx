import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";

interface LeaveAttemptDialogProps {
  open: boolean;
  onStay: () => void;
  onLeave: () => void;
}

export function LeaveAttemptDialog({ open, onStay, onLeave }: LeaveAttemptDialogProps) {
  return (
    <Dialog open={open} onClose={onStay} fullWidth maxWidth="xs">
      <DialogTitle>Leave this attempt?</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Your attempt is still in progress and the timer keeps running. Your saved answers
          stay intact, but you'll need to come back and submit before time runs out.
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onLeave} color="error">
          Leave anyway
        </Button>
        <Button onClick={onStay} variant="contained" autoFocus>
          Stay on this page
        </Button>
      </DialogActions>
    </Dialog>
  );
}

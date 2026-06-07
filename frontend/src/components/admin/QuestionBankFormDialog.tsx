import { useState, type FormEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
} from "@mui/material";
import { isAxiosError } from "axios";

import type { ApiErrorResponse, QuestionBank } from "../../api/types";

export type QuestionBankFormMode = "create" | "edit";

interface QuestionBankFormValues {
  name: string;
  description: string;
}

interface QuestionBankFormDialogProps {
  open: boolean;
  mode: QuestionBankFormMode;
  bank?: QuestionBank | null;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onSubmit: (values: QuestionBankFormValues) => void;
}

const EMPTY_VALUES: QuestionBankFormValues = { name: "", description: "" };

interface QuestionBankFormProps {
  mode: QuestionBankFormMode;
  initialValues: QuestionBankFormValues;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onSubmit: (values: QuestionBankFormValues) => void;
}

function QuestionBankForm({
  mode,
  initialValues,
  submitting,
  error,
  onClose,
  onSubmit,
}: QuestionBankFormProps) {
  const [values, setValues] = useState<QuestionBankFormValues>(initialValues);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(values);
  };

  const errorMessage = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  const title = mode === "create" ? "Create question bank" : "Edit question bank";
  const submitLabel = mode === "create" ? "Create" : "Save changes";
  const pendingLabel = mode === "create" ? "Creating..." : "Saving...";

  return (
    <>
      <DialogTitle>{title}</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {error !== null && error !== undefined && (
            <Alert severity="error">
              {errorMessage ?? "Something went wrong. Please try again."}
            </Alert>
          )}
          <TextField
            label="Name"
            value={values.name}
            onChange={(e) => setValues((prev) => ({ ...prev, name: e.target.value }))}
            required
            fullWidth
            autoFocus
          />
          <TextField
            label="Description"
            value={values.description}
            onChange={(e) =>
              setValues((prev) => ({ ...prev, description: e.target.value }))
            }
            fullWidth
            multiline
            minRows={3}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={submitting}>
            {submitting ? pendingLabel : submitLabel}
          </Button>
        </DialogActions>
      </Box>
    </>
  );
}

export function QuestionBankFormDialog({
  open,
  mode,
  bank,
  submitting,
  error,
  onClose,
  onSubmit,
}: QuestionBankFormDialogProps) {
  const initialValues: QuestionBankFormValues = bank
    ? { name: bank.name, description: bank.description ?? "" }
    : EMPTY_VALUES;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      {open && (
        <QuestionBankForm
          key={bank?.id ?? "create"}
          mode={mode}
          initialValues={initialValues}
          submitting={submitting}
          error={error}
          onClose={onClose}
          onSubmit={onSubmit}
        />
      )}
    </Dialog>
  );
}

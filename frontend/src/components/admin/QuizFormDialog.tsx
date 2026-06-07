import { useState, type FormEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { isAxiosError } from "axios";

import type { ApiErrorResponse, Quiz } from "../../api/types";

export type QuizFormMode = "create" | "edit";

export interface QuizFormSubmitValues {
  title: string;
  description: string;
  durationMinutes: number;
  startTime: string | null;
  endTime: string | null;
  shuffleQuestions: boolean;
  shuffleOptions: boolean;
  maxAttempts: number;
  proctoringEnabled: boolean;
  maxTabSwitches: number | null;
}

interface QuizFormDialogProps {
  open: boolean;
  mode: QuizFormMode;
  quiz?: Quiz | null;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onSubmit: (values: QuizFormSubmitValues) => void;
}

interface FormValues {
  title: string;
  description: string;
  durationMinutes: string;
  startTime: string;
  endTime: string;
  shuffleQuestions: boolean;
  shuffleOptions: boolean;
  maxAttempts: string;
  proctoringEnabled: boolean;
  maxTabSwitches: string;
}

/** Converts an ISO timestamp to a `datetime-local` input value in the browser's local time. */
function toDatetimeLocal(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

/** Converts a `datetime-local` input value (interpreted as local time) back to ISO. */
function fromDatetimeLocal(value: string): string | null {
  if (!value) return null;
  return new Date(value).toISOString();
}

function buildInitialValues(quiz: Quiz | null | undefined): FormValues {
  if (quiz) {
    return {
      title: quiz.title,
      description: quiz.description ?? "",
      durationMinutes: String(quiz.duration_minutes),
      startTime: toDatetimeLocal(quiz.start_time),
      endTime: toDatetimeLocal(quiz.end_time),
      shuffleQuestions: quiz.shuffle_questions,
      shuffleOptions: quiz.shuffle_options,
      maxAttempts: String(quiz.max_attempts),
      proctoringEnabled: quiz.proctoring_enabled,
      maxTabSwitches: quiz.max_tab_switches !== null ? String(quiz.max_tab_switches) : "",
    };
  }

  return {
    title: "",
    description: "",
    durationMinutes: "60",
    startTime: "",
    endTime: "",
    shuffleQuestions: false,
    shuffleOptions: false,
    maxAttempts: "1",
    proctoringEnabled: false,
    maxTabSwitches: "",
  };
}

interface QuizFormProps {
  mode: QuizFormMode;
  initialValues: FormValues;
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onSubmit: (values: QuizFormSubmitValues) => void;
}

function QuizForm({ mode, initialValues, submitting, error, onClose, onSubmit }: QuizFormProps) {
  const [values, setValues] = useState<FormValues>(initialValues);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      title: values.title,
      description: values.description,
      durationMinutes: Number(values.durationMinutes),
      startTime: fromDatetimeLocal(values.startTime),
      endTime: fromDatetimeLocal(values.endTime),
      shuffleQuestions: values.shuffleQuestions,
      shuffleOptions: values.shuffleOptions,
      maxAttempts: Number(values.maxAttempts),
      proctoringEnabled: values.proctoringEnabled,
      maxTabSwitches:
        values.proctoringEnabled && values.maxTabSwitches !== ""
          ? Number(values.maxTabSwitches)
          : null,
    });
  };

  const errorMessage = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  const title = mode === "create" ? "Create quiz" : "Edit quiz metadata";
  const submitLabel = mode === "create" ? "Create" : "Save changes";
  const pendingLabel = mode === "create" ? "Creating..." : "Saving...";

  return (
    <>
      <DialogTitle>{title}</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2.5 }}>
          {error !== null && error !== undefined && (
            <Alert severity="error">
              {errorMessage ?? "Something went wrong. Please try again."}
            </Alert>
          )}

          <TextField
            label="Title"
            value={values.title}
            onChange={(e) => setValues((prev) => ({ ...prev, title: e.target.value }))}
            required
            fullWidth
            autoFocus
          />
          <TextField
            label="Description (optional)"
            value={values.description}
            onChange={(e) => setValues((prev) => ({ ...prev, description: e.target.value }))}
            fullWidth
            multiline
            minRows={2}
          />

          <Stack direction="row" spacing={2}>
            <TextField
              label="Duration (minutes)"
              type="number"
              value={values.durationMinutes}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, durationMinutes: e.target.value }))
              }
              required
              fullWidth
              slotProps={{ htmlInput: { min: 1, step: 1 } }}
            />
            <TextField
              label="Max attempts"
              type="number"
              value={values.maxAttempts}
              onChange={(e) => setValues((prev) => ({ ...prev, maxAttempts: e.target.value }))}
              required
              fullWidth
              slotProps={{ htmlInput: { min: 1, step: 1 } }}
            />
          </Stack>

          <Stack direction="row" spacing={2}>
            <TextField
              label="Start time (optional)"
              type="datetime-local"
              value={values.startTime}
              onChange={(e) => setValues((prev) => ({ ...prev, startTime: e.target.value }))}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              label="End time (optional)"
              type="datetime-local"
              value={values.endTime}
              onChange={(e) => setValues((prev) => ({ ...prev, endTime: e.target.value }))}
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>
          <Typography variant="caption" color="text.secondary">
            Times are interpreted in your browser's local timezone. Leave blank for an
            unrestricted time window.
          </Typography>

          <Stack direction="row" spacing={3} sx={{ flexWrap: "wrap" }}>
            <FormControlLabel
              control={
                <Switch
                  checked={values.shuffleQuestions}
                  onChange={(e) =>
                    setValues((prev) => ({ ...prev, shuffleQuestions: e.target.checked }))
                  }
                />
              }
              label="Shuffle questions"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={values.shuffleOptions}
                  onChange={(e) =>
                    setValues((prev) => ({ ...prev, shuffleOptions: e.target.checked }))
                  }
                />
              }
              label="Shuffle options"
            />
          </Stack>

          <FormControlLabel
            control={
              <Switch
                checked={values.proctoringEnabled}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, proctoringEnabled: e.target.checked }))
                }
              />
            }
            label="Proctoring enabled"
          />
          {values.proctoringEnabled && (
            <TextField
              label="Max tab switches (optional)"
              type="number"
              value={values.maxTabSwitches}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, maxTabSwitches: e.target.value }))
              }
              fullWidth
              slotProps={{ htmlInput: { min: 0, step: 1 } }}
              helperText="Leave blank for no limit"
            />
          )}
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

export function QuizFormDialog({
  open,
  mode,
  quiz,
  submitting,
  error,
  onClose,
  onSubmit,
}: QuizFormDialogProps) {
  const initialValues = buildInitialValues(quiz);

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      {open && (
        <QuizForm
          key={quiz?.id ?? "create"}
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

import { useState, type FormEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { isAxiosError } from "axios";

import type { ApiErrorResponse, OptionInput, Question, QuestionBank } from "../../api/types";

export type QuestionFormMode = "create" | "edit";

const OPTION_COUNT = 4;

export interface QuestionFormSubmitValues {
  bankId: string;
  text: string;
  explanation: string;
  marks: number;
  negativeMarks: number;
  options: OptionInput[];
}

interface QuestionFormDialogProps {
  open: boolean;
  mode: QuestionFormMode;
  question?: Question | null;
  banks: QuestionBank[];
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onSubmit: (values: QuestionFormSubmitValues) => void;
}

interface FormValues {
  bankId: string;
  text: string;
  explanation: string;
  marks: string;
  negativeMarks: string;
  optionTexts: string[];
  correctIndex: number;
}

function buildInitialValues(question: Question | null | undefined, defaultBankId: string): FormValues {
  if (question) {
    const correctIndex = Math.max(
      0,
      question.options.findIndex((opt) => opt.is_correct),
    );
    return {
      bankId: question.questionBankId,
      text: question.text,
      explanation: question.explanation ?? "",
      marks: String(question.marks),
      negativeMarks: String(question.negativeMarks),
      optionTexts: question.options.map((opt) => opt.text),
      correctIndex,
    };
  }

  return {
    bankId: defaultBankId,
    text: "",
    explanation: "",
    marks: "1",
    negativeMarks: "0",
    optionTexts: Array.from({ length: OPTION_COUNT }, () => ""),
    correctIndex: 0,
  };
}

interface QuestionFormProps {
  mode: QuestionFormMode;
  initialValues: FormValues;
  banks: QuestionBank[];
  submitting: boolean;
  error: unknown;
  onClose: () => void;
  onSubmit: (values: QuestionFormSubmitValues) => void;
}

function QuestionForm({
  mode,
  initialValues,
  banks,
  submitting,
  error,
  onClose,
  onSubmit,
}: QuestionFormProps) {
  const [values, setValues] = useState<FormValues>(initialValues);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      bankId: values.bankId,
      text: values.text,
      explanation: values.explanation,
      marks: Number(values.marks),
      negativeMarks: Number(values.negativeMarks),
      options: values.optionTexts.map((text, index) => ({
        text,
        is_correct: index === values.correctIndex,
      })),
    });
  };

  const setOptionText = (index: number, text: string) => {
    setValues((prev) => ({
      ...prev,
      optionTexts: prev.optionTexts.map((value, i) => (i === index ? text : value)),
    }));
  };

  const errorMessage = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : undefined;

  const title = mode === "create" ? "Create question" : "Edit question";
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

          <FormControl fullWidth required disabled={mode === "edit"}>
            <InputLabel id="question-bank-label">Question bank</InputLabel>
            <Select
              labelId="question-bank-label"
              label="Question bank"
              value={values.bankId}
              onChange={(e) => setValues((prev) => ({ ...prev, bankId: e.target.value }))}
            >
              {banks.map((bank) => (
                <MenuItem key={bank.id} value={bank.id}>
                  {bank.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Question text"
            value={values.text}
            onChange={(e) => setValues((prev) => ({ ...prev, text: e.target.value }))}
            required
            fullWidth
            multiline
            minRows={2}
            autoFocus
          />

          <TextField
            label="Explanation (optional)"
            value={values.explanation}
            onChange={(e) => setValues((prev) => ({ ...prev, explanation: e.target.value }))}
            fullWidth
            multiline
            minRows={2}
          />

          <Stack direction="row" spacing={2}>
            <TextField
              label="Marks"
              type="number"
              value={values.marks}
              onChange={(e) => setValues((prev) => ({ ...prev, marks: e.target.value }))}
              required
              fullWidth
              slotProps={{ htmlInput: { min: 0.01, step: 0.01 } }}
            />
            <TextField
              label="Negative marks"
              type="number"
              value={values.negativeMarks}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, negativeMarks: e.target.value }))
              }
              required
              fullWidth
              slotProps={{ htmlInput: { min: 0, step: 0.01 } }}
            />
          </Stack>

          <FormControl component="fieldset" fullWidth>
            <FormLabel component="legend">Options — select the correct one</FormLabel>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1 }}>
              Exactly 4 options are required, with exactly one marked correct.
            </Typography>
            <RadioGroup
              value={String(values.correctIndex)}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, correctIndex: Number(e.target.value) }))
              }
            >
              <Stack spacing={1.5}>
                {values.optionTexts.map((text, index) => (
                  <Stack key={index} direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    <FormControlLabel
                      value={String(index)}
                      control={<Radio />}
                      label=""
                      sx={{ m: 0 }}
                    />
                    <TextField
                      label={`Option ${index + 1}`}
                      value={text}
                      onChange={(e) => setOptionText(index, e.target.value)}
                      required
                      fullWidth
                      size="small"
                    />
                  </Stack>
                ))}
              </Stack>
            </RadioGroup>
          </FormControl>
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

export function QuestionFormDialog({
  open,
  mode,
  question,
  banks,
  submitting,
  error,
  onClose,
  onSubmit,
}: QuestionFormDialogProps) {
  const initialValues = buildInitialValues(question, banks[0]?.id ?? "");

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      {open && (
        <QuestionForm
          key={question?.id ?? "create"}
          mode={mode}
          initialValues={initialValues}
          banks={banks}
          submitting={submitting}
          error={error}
          onClose={onClose}
          onSubmit={onSubmit}
        />
      )}
    </Dialog>
  );
}

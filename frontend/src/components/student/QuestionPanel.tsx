import {
  Box,
  Button,
  FormControl,
  FormControlLabel,
  Paper,
  Radio,
  RadioGroup,
  Stack,
  Typography,
} from "@mui/material";

import type { AttemptQuestionRecord } from "../../api/types";
import { SaveStatusIndicator, type SaveStatus } from "./SaveStatusIndicator";

interface QuestionPanelProps {
  question: AttemptQuestionRecord;
  questionNumber: number;
  totalQuestions: number;
  selectedOptionId: string | null;
  saveStatus: SaveStatus;
  disabled?: boolean;
  onSelect: (optionId: string) => void;
  onClear: () => void;
}

export function QuestionPanel({
  question,
  questionNumber,
  totalQuestions,
  selectedOptionId,
  saveStatus,
  disabled = false,
  onSelect,
  onClear,
}: QuestionPanelProps) {
  return (
    <Paper variant="outlined" sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack
        direction="row"
        sx={{ alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 1 }}
      >
        <Typography variant="overline" color="text.secondary">
          Question {questionNumber} of {totalQuestions} &middot; {question.marks} marks
          {question.negative_marks > 0 ? ` · -${question.negative_marks} for incorrect` : ""}
        </Typography>
        <SaveStatusIndicator status={saveStatus} />
      </Stack>

      <Typography variant="h6">{question.question_text_snapshot}</Typography>

      <FormControl disabled={disabled}>
        <RadioGroup
          value={selectedOptionId ?? ""}
          onChange={(event) => onSelect(event.target.value)}
        >
          {question.options.map((option) => (
            <FormControlLabel
              key={option.id}
              value={option.id}
              control={<Radio />}
              label={option.option_text_snapshot}
            />
          ))}
        </RadioGroup>
      </FormControl>

      <Box>
        <Button
          size="small"
          color="inherit"
          disabled={disabled || selectedOptionId === null}
          onClick={onClear}
        >
          Clear answer
        </Button>
      </Box>
    </Paper>
  );
}

import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RemoveCircleIcon from "@mui/icons-material/RemoveCircle";
import {
  Box,
  Button,
  Chip,
  Grid,
  Paper,
  Radio,
  Stack,
  Typography,
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import { isAxiosError } from "axios";
import { Link as RouterLink, useParams } from "react-router-dom";

import type { ApiErrorResponse, AttemptQuestionResultRecord } from "../../api/types";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { ROUTES } from "../../constants/routes";
import { useAttemptResultQuery } from "../../hooks/useAttempts";

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatDateTime(value: string | null): string {
  return value ? dateTimeFormatter.format(new Date(value)) : "—";
}

const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  timed_out: "Timed out",
  abandoned: "Abandoned",
  in_progress: "In progress",
};

export function AttemptResultPage() {
  const { attemptId = "" } = useParams<{ attemptId: string }>();
  const { data: result, isPending, isError, error, refetch } = useAttemptResultQuery(attemptId);

  if (isPending) {
    return <LoadingState message="Loading your result..." />;
  }

  if (isError) {
    const detail = isAxiosError<ApiErrorResponse>(error) ? error.response?.data?.detail : undefined;
    const status = isAxiosError(error) ? error.response?.status : undefined;

    return (
      <ErrorState
        title={status === 404 ? "Result not found" : "Failed to load your result"}
        message={detail ?? "Please try again."}
        onRetry={status === 404 ? undefined : () => refetch()}
      />
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 1 }}>
        <Typography variant="h4">Quiz result</Typography>
        <Button component={RouterLink} to={ROUTES.student.quizzes} startIcon={<ArrowBackIcon />}>
          Back to quizzes
        </Button>
      </Stack>

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="overline" color="text.secondary">
              Status
            </Typography>
            <Typography variant="h6">{STATUS_LABELS[result.status] ?? result.status}</Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="overline" color="text.secondary">
              Score
            </Typography>
            <Typography variant="h6">{result.score}</Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="overline" color="text.secondary">
              Percentage
            </Typography>
            <Typography variant="h6">{result.percentage}%</Typography>
          </Grid>
          <Grid size={{ xs: 6, sm: 3 }}>
            <Typography variant="overline" color="text.secondary">
              Attempt
            </Typography>
            <Typography variant="h6">#{result.attempt_number}</Typography>
          </Grid>
        </Grid>

        <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: "wrap" }}>
          <Chip size="small" color="success" variant="outlined" label={`Correct: ${result.correct_count}`} />
          <Chip size="small" color="error" variant="outlined" label={`Incorrect: ${result.incorrect_count}`} />
          <Chip size="small" color="default" variant="outlined" label={`Unanswered: ${result.unanswered_count}`} />
        </Stack>

        <Stack direction="row" spacing={3} sx={{ mt: 2, flexWrap: "wrap" }}>
          <Typography variant="body2" color="text.secondary">
            Started: {formatDateTime(result.started_at)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Submitted: {formatDateTime(result.submitted_at)}
          </Typography>
        </Stack>
      </Paper>

      <Stack spacing={2}>
        {result.questions.map((question, index) => (
          <ResultQuestionCard key={question.id} question={question} index={index} />
        ))}
      </Stack>
    </Box>
  );
}

interface ResultQuestionCardProps {
  question: AttemptQuestionResultRecord;
  index: number;
}

function ResultQuestionCard({ question, index }: ResultQuestionCardProps) {
  const outcomeChip =
    question.is_correct === null ? (
      <Chip size="small" icon={<RemoveCircleIcon />} label="Unanswered" color="default" variant="outlined" />
    ) : question.is_correct ? (
      <Chip size="small" icon={<CheckCircleIcon />} label="Correct" color="success" variant="outlined" />
    ) : (
      <Chip size="small" icon={<CancelIcon />} label="Incorrect" color="error" variant="outlined" />
    );

  return (
    <Paper variant="outlined" sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 1 }}>
        <Typography variant="overline" color="text.secondary">
          Question {index + 1} &middot; {question.marks} marks
          {question.negative_marks > 0 ? ` · -${question.negative_marks} for incorrect` : ""}
          {question.marks_awarded !== null ? ` · awarded ${question.marks_awarded}` : ""}
        </Typography>
        {outcomeChip}
      </Stack>

      <Typography variant="h6">{question.question_text_snapshot}</Typography>

      <Stack spacing={1}>
        {question.options.map((option) => {
          const isSelected = option.id === question.selected_option_id;
          const isCorrectOption = option.is_correct_snapshot;

          let color: "success" | "error" | undefined;
          if (isCorrectOption) color = "success";
          else if (isSelected && !isCorrectOption) color = "error";

          return (
            <Box
              key={option.id}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                px: 1.5,
                py: 0.5,
                borderRadius: 1,
                border: "1px solid",
                borderColor: color ? `${color}.main` : "divider",
                bgcolor: color
                  ? (theme) => alpha(theme.palette[color as "success" | "error"].main, 0.08)
                  : "transparent",
              }}
            >
              <Radio checked={isSelected} disabled size="small" />
              <Typography variant="body2" sx={{ flexGrow: 1 }}>
                {option.option_text_snapshot}
              </Typography>
              {isCorrectOption && (
                <Chip size="small" label="Correct answer" color="success" variant="outlined" />
              )}
              {isSelected && !isCorrectOption && (
                <Chip size="small" label="Your answer" color="error" variant="outlined" />
              )}
            </Box>
          );
        })}
      </Stack>
    </Paper>
  );
}

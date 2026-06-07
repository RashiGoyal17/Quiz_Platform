import { useMemo, useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import DeleteIcon from "@mui/icons-material/Delete";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { Link as RouterLink, useParams } from "react-router-dom";

import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { PublishQuizDialog, type PublishQuizMode } from "../../components/admin/PublishQuizDialog";
import { QuestionPickerDialog } from "../../components/admin/QuestionPickerDialog";
import { RemoveQuizQuestionDialog } from "../../components/admin/RemoveQuizQuestionDialog";
import { ROUTES } from "../../constants/routes";
import type { QuizQuestion } from "../../api/types";
import { usePublishQuizMutation, useQuizQuery, useUnpublishQuizMutation } from "../../hooks/useQuizzes";
import {
  useMoveQuizQuestionMutation,
  useQuizQuestionsQuery,
  useRemoveQuestionFromQuizMutation,
} from "../../hooks/useQuizQuestions";

const PREVIEW_LENGTH = 160;

function previewText(text: string): string {
  return text.length > PREVIEW_LENGTH ? `${text.slice(0, PREVIEW_LENGTH)}…` : text;
}

interface ReadinessCheck {
  label: string;
  met: boolean;
  hint?: string;
}

function buildReadinessChecks(
  quiz: { title: string; duration_minutes: number; start_time: string | null; end_time: string | null } | undefined,
  questionCount: number,
): ReadinessCheck[] {
  const titlePresent = Boolean(quiz?.title.trim());
  const durationValid = Boolean(quiz && quiz.duration_minutes > 0);
  const timeWindowValid =
    !quiz?.start_time || !quiz?.end_time || new Date(quiz.start_time) < new Date(quiz.end_time);

  return [
    { label: "Title is present", met: titlePresent },
    { label: "Duration is valid (greater than zero)", met: durationValid },
    {
      label: "Time window is valid",
      met: timeWindowValid,
      hint: "If both start and end times are set, the start must be before the end.",
    },
    {
      label: "At least one question is assigned",
      met: questionCount > 0,
      hint: "Add at least one question before publishing.",
    },
  ];
}

export function QuizBuilderPage() {
  const { quizId = "" } = useParams<{ quizId: string }>();

  const quizQuery = useQuizQuery(quizId);
  const quizQuestionsQuery = useQuizQuestionsQuery(quizId);

  const [pickerOpen, setPickerOpen] = useState(false);
  const [removeTarget, setRemoveTarget] = useState<QuizQuestion | null>(null);
  const [publishMode, setPublishMode] = useState<PublishQuizMode | null>(null);

  const removeMutation = useRemoveQuestionFromQuizMutation();
  const moveMutation = useMoveQuizQuestionMutation();
  const publishMutation = usePublishQuizMutation();
  const unpublishMutation = useUnpublishQuizMutation();

  const quiz = quizQuery.data;
  const quizQuestions = useMemo(
    () => [...(quizQuestionsQuery.data ?? [])].sort((a, b) => a.position - b.position),
    [quizQuestionsQuery.data],
  );
  const assignedQuestionIds = useMemo(
    () => new Set(quizQuestions.map((qq) => qq.question_id)),
    [quizQuestions],
  );

  const readinessChecks = buildReadinessChecks(quiz, quizQuestions.length);
  const isReadyToPublish = readinessChecks.every((check) => check.met);

  const closeRemoveDialog = () => {
    setRemoveTarget(null);
    removeMutation.reset();
  };

  const closePublishDialog = () => {
    setPublishMode(null);
    publishMutation.reset();
    unpublishMutation.reset();
  };

  const handleRemoveConfirm = () => {
    if (!removeTarget) return;
    removeMutation.mutate(
      { quizId, questionId: removeTarget.question_id },
      { onSuccess: () => closeRemoveDialog() },
    );
  };

  const handlePublishConfirm = () => {
    if (publishMode === "publish") {
      publishMutation.mutate(quizId, { onSuccess: () => closePublishDialog() });
    } else if (publishMode === "unpublish") {
      unpublishMutation.mutate(quizId, { onSuccess: () => closePublishDialog() });
    }
  };

  const handleMove = (index: number, direction: "up" | "down") => {
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= quizQuestions.length) return;

    const [first, second] =
      direction === "up"
        ? [quizQuestions[targetIndex], quizQuestions[index]]
        : [quizQuestions[index], quizQuestions[targetIndex]];

    moveMutation.mutate({ quizId, first, second });
  };

  if (quizQuery.isPending || quizQuestionsQuery.isPending) {
    return <LoadingState message="Loading quiz..." />;
  }

  if (quizQuery.isError || !quiz) {
    return (
      <ErrorState
        title="Failed to load quiz"
        message={quizQuery.error instanceof Error ? quizQuery.error.message : "Please try again."}
        onRetry={() => quizQuery.refetch()}
      />
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack direction="row" sx={{ alignItems: "center", gap: 1 }}>
        <IconButton component={RouterLink} to={ROUTES.admin.quizzes} aria-label="Back to quizzes">
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4">{quiz.title}</Typography>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center", mt: 0.5 }}>
            <Chip
              size="small"
              label={quiz.is_published ? "Published" : "Draft"}
              color={quiz.is_published ? "success" : "default"}
              variant={quiz.is_published ? "filled" : "outlined"}
            />
            <Typography variant="body2" color="text.secondary">
              {quiz.duration_minutes} minutes · Max attempts {quiz.max_attempts}
            </Typography>
          </Stack>
        </Box>
        {quiz.is_published ? (
          <Button
            variant="outlined"
            color="warning"
            startIcon={<StopIcon />}
            onClick={() => setPublishMode("unpublish")}
          >
            Unpublish
          </Button>
        ) : (
          <Tooltip
            title={
              isReadyToPublish
                ? ""
                : "This quiz is not ready to publish yet — see the publish readiness checklist below."
            }
          >
            <span>
              <Button
                variant="contained"
                startIcon={<PlayArrowIcon />}
                disabled={!isReadyToPublish}
                onClick={() => setPublishMode("publish")}
              >
                Publish
              </Button>
            </span>
          </Tooltip>
        )}
      </Stack>

      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Publish readiness
          </Typography>
          <List dense disablePadding>
            {readinessChecks.map((check) => (
              <ListItem key={check.label} disableGutters>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {check.met ? (
                    <CheckCircleIcon color="success" fontSize="small" />
                  ) : (
                    <CancelIcon color="error" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={check.label}
                  secondary={!check.met ? check.hint : undefined}
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between" }}>
        <Typography variant="h6">
          Questions ({quizQuestions.length})
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setPickerOpen(true)}>
          Add questions
        </Button>
      </Stack>

      {quizQuestions.length === 0 ? (
        <EmptyState
          title="No questions assigned yet"
          message="Add questions from your question banks to build this quiz."
          action={
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setPickerOpen(true)}>
              Add questions
            </Button>
          }
        />
      ) : (
        <Card variant="outlined">
          <List disablePadding>
            {quizQuestions.map((quizQuestion, index) => {
              const effectiveMarks = quizQuestion.marks_override ?? quizQuestion.question.marks;
              return (
                <ListItem
                  key={quizQuestion.question_id}
                  divider={index < quizQuestions.length - 1}
                  secondaryAction={
                    <Stack direction="row" spacing={0.5}>
                      <Tooltip title="Move up">
                        <span>
                          <IconButton
                            size="small"
                            aria-label="Move question up"
                            disabled={index === 0 || moveMutation.isPending}
                            onClick={() => handleMove(index, "up")}
                          >
                            <ArrowUpwardIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="Move down">
                        <span>
                          <IconButton
                            size="small"
                            aria-label="Move question down"
                            disabled={index === quizQuestions.length - 1 || moveMutation.isPending}
                            onClick={() => handleMove(index, "down")}
                          >
                            <ArrowDownwardIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title="Remove from quiz">
                        <IconButton
                          size="small"
                          aria-label="Remove question from quiz"
                          onClick={() => setRemoveTarget(quizQuestion)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Stack>
                  }
                >
                  <ListItemText
                    primary={`${quizQuestion.position + 1}. ${previewText(quizQuestion.question.text)}`}
                    secondary={
                      <Box component="span" sx={{ display: "flex", gap: 1, alignItems: "center", mt: 0.5 }}>
                        <Tooltip title="Marks editing through the UI is deferred until the backend supports updating quiz questions directly.">
                          <Chip size="small" label={`${effectiveMarks} marks`} variant="outlined" />
                        </Tooltip>
                        {quizQuestion.marks_override !== null && (
                          <Typography component="span" variant="caption" color="text.secondary">
                            (overridden from {quizQuestion.question.marks})
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              );
            })}
          </List>
        </Card>
      )}

      {moveMutation.isError && (
        <Alert severity="error" onClose={() => moveMutation.reset()}>
          Unable to reorder questions. Please try again.
        </Alert>
      )}

      <QuestionPickerDialog
        open={pickerOpen}
        quizId={quizId}
        assignedQuestionIds={assignedQuestionIds}
        nextPosition={quizQuestions.length}
        onClose={() => setPickerOpen(false)}
      />

      <RemoveQuizQuestionDialog
        open={removeTarget !== null}
        quizQuestion={removeTarget}
        submitting={removeMutation.isPending}
        error={removeMutation.error}
        onClose={closeRemoveDialog}
        onConfirm={handleRemoveConfirm}
      />

      <PublishQuizDialog
        open={publishMode !== null}
        mode={publishMode ?? "publish"}
        quiz={quiz}
        submitting={publishMutation.isPending || unpublishMutation.isPending}
        error={publishMode === "unpublish" ? unpublishMutation.error : publishMutation.error}
        onClose={closePublishDialog}
        onConfirm={handlePublishConfirm}
      />
    </Box>
  );
}

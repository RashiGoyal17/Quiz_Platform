import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Alert, Box, Button, Grid, Paper, Snackbar, Stack, Typography } from "@mui/material";
import { isAxiosError } from "axios";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link as RouterLink, Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";

import type { ApiErrorResponse, TabSwitchResponse } from "../../api/types";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { QuestionNavigator } from "../../components/student/QuestionNavigator";
import { QuestionPanel } from "../../components/student/QuestionPanel";
import { QuizTimer } from "../../components/student/QuizTimer";
import { SubmitAttemptDialog } from "../../components/student/SubmitAttemptDialog";
import type { SaveStatus } from "../../components/student/SaveStatusIndicator";
import { ROUTES } from "../../constants/routes";
import { useAntiCheatTracking } from "../../hooks/useAntiCheatTracking";
import {
  useAttemptQuery,
  useAttemptResultQuery,
  useSaveAnswerMutation,
  useSubmitAttemptMutation,
} from "../../hooks/useAttempts";

function getErrorMessage(error: unknown): string | undefined {
  return isAxiosError<ApiErrorResponse>(error) ? error.response?.data?.detail : undefined;
}

export function AttemptDetailPage() {
  const { attemptId = "" } = useParams<{ attemptId: string }>();
  const [searchParams] = useSearchParams();
  const quizId = searchParams.get("quizId");
  const navigate = useNavigate();

  const attemptQuery = useAttemptQuery(attemptId, quizId);
  const fallbackResultQuery = useAttemptResultQuery(attemptId, !quizId);

  const attempt = attemptQuery.data;

  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [saveStatuses, setSaveStatuses] = useState<Record<string, SaveStatus>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
  const [awayBannerOpen, setAwayBannerOpen] = useState(false);
  const [lockNotice, setLockNotice] = useState<string | null>(null);
  const [isFinalized, setIsFinalized] = useState(false);

  const initializedRef = useRef(false);
  const hasFinalizedRef = useRef(false);

  const saveAnswerMutation = useSaveAnswerMutation(attemptId);
  const submitMutation = useSubmitAttemptMutation(attemptId);

  useEffect(() => {
    if (attempt && !initializedRef.current) {
      initializedRef.current = true;
      const initialAnswers: Record<string, string | null> = {};
      for (const question of attempt.questions) {
        initialAnswers[question.id] = question.selected_option_id;
      }
      setAnswers(initialAnswers);
    }
  }, [attempt]);

  const isInProgress = attempt?.status === "in_progress";

  const finalizeAndGoToResult = (reason?: string) => {
    if (hasFinalizedRef.current) return;
    hasFinalizedRef.current = true;
    setIsFinalized(true);
    if (reason) setLockNotice(reason);
    navigate(ROUTES.student.attemptResult(attemptId), { replace: true });
  };

  const handleSubmit = () => {
    if (hasFinalizedRef.current) return;
    hasFinalizedRef.current = true;
    setIsFinalized(true);
    submitMutation.mutate(undefined, {
      onSuccess: () => {
        setSubmitDialogOpen(false);
        navigate(ROUTES.student.attemptResult(attemptId), { replace: true });
      },
      onError: () => {
        hasFinalizedRef.current = false;
        setIsFinalized(false);
      },
    });
  };

  const handleTimerExpire = () => {
    if (hasFinalizedRef.current || submitMutation.isPending) return;
    handleSubmit();
  };

  const handleTabSwitchLogged = (result: TabSwitchResponse) => {
    if (result.limit_exceeded) {
      finalizeAndGoToResult(
        "Your attempt was abandoned because you exceeded the allowed number of tab switches.",
      );
    }
  };

  useAntiCheatTracking({
    attemptId,
    active: Boolean(attempt) && isInProgress && !isFinalized,
    onTabSwitchLogged: handleTabSwitchLogged,
    onWindowBlur: () => setAwayBannerOpen(true),
    onWindowFocus: () => setAwayBannerOpen(false),
  });

  const handleSelectOption = (questionId: string, optionId: string | null) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionId }));
    setSaveStatuses((prev) => ({ ...prev, [questionId]: "saving" }));
    saveAnswerMutation.mutate(
      { attempt_question_id: questionId, selected_option_id: optionId },
      {
        onSuccess: () => {
          setSaveStatuses((prev) => ({ ...prev, [questionId]: "saved" }));
        },
        onError: () => {
          setSaveStatuses((prev) => ({ ...prev, [questionId]: "error" }));
        },
      },
    );
  };

  const answeredFlags = useMemo(
    () => attempt?.questions.map((question) => Boolean(answers[question.id])) ?? [],
    [attempt, answers],
  );
  const unansweredCount = answeredFlags.filter((flag) => !flag).length;

  // ---- Routing / loading / error states -------------------------------------------------

  if (quizId) {
    if (attemptQuery.isPending) {
      return <LoadingState message="Loading your attempt..." />;
    }

    if (attemptQuery.isError) {
      const status = isAxiosError(attemptQuery.error) ? attemptQuery.error.response?.status : undefined;
      const detail = getErrorMessage(attemptQuery.error);

      if (status === 404) {
        return (
          <ErrorState
            title="Attempt not found"
            message={detail ?? "This attempt doesn't exist or you don't have access to it."}
          />
        );
      }
      if (status === 403) {
        return (
          <ErrorState
            title="Unauthorized"
            message={detail ?? "You don't have permission to view this attempt."}
          />
        );
      }
      if (status === 400) {
        return (
          <ErrorState
            title="Unable to open this attempt"
            message={detail ?? "This quiz can no longer be attempted."}
          />
        );
      }
      return (
        <ErrorState
          title="Failed to load your attempt"
          message={detail ?? "A network error occurred. Please check your connection and try again."}
          onRetry={() => attemptQuery.refetch()}
        />
      );
    }

    if (attempt && !isInProgress) {
      return <Navigate to={ROUTES.student.attemptResult(attemptId)} replace />;
    }
  } else {
    if (fallbackResultQuery.isPending) {
      return <LoadingState message="Loading your attempt..." />;
    }

    if (fallbackResultQuery.isSuccess) {
      return <Navigate to={ROUTES.student.attemptResult(attemptId)} replace />;
    }

    return (
      <ErrorState
        title="Can't resume this attempt"
        message="This attempt can't be reloaded directly. Please return to the quiz list and resume it from there."
      />
    );
  }

  if (!attempt) {
    return <LoadingState message="Loading your attempt..." />;
  }

  const currentQuestion = attempt.questions[currentIndex];
  const submitErrorMessage = submitMutation.isError ? getErrorMessage(submitMutation.error) : null;
  const deadline = new Date(attempt.started_at).getTime() + attempt.time_limit_minutes * 60_000;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack
        direction="row"
        sx={{ alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 2 }}
      >
        <Box>
          <Typography variant="h4">Quiz in progress</Typography>
          <Typography variant="body2" color="text.secondary">
            Attempt #{attempt.attempt_number} &middot; {attempt.questions.length} questions
          </Typography>
        </Box>
        <QuizTimer deadline={deadline} onExpire={handleTimerExpire} />
      </Stack>

      {lockNotice && <Alert severity="warning">{lockNotice}</Alert>}

      <Snackbar
        open={awayBannerOpen}
        message="You navigated away from the quiz window. This activity may be recorded."
      />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Stack spacing={2}>
            <QuestionNavigator
              total={attempt.questions.length}
              currentIndex={currentIndex}
              answeredFlags={answeredFlags}
              onJump={setCurrentIndex}
            />
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Answered {answeredFlags.filter(Boolean).length} of {attempt.questions.length}
              </Typography>
              <Button
                variant="contained"
                fullWidth
                sx={{ mt: 1.5 }}
                onClick={() => setSubmitDialogOpen(true)}
              >
                Submit attempt
              </Button>
            </Paper>
          </Stack>
        </Grid>

        <Grid size={{ xs: 12, md: 8 }}>
          <Stack spacing={2}>
            {currentQuestion && (
              <QuestionPanel
                key={currentQuestion.id}
                question={currentQuestion}
                questionNumber={currentIndex + 1}
                totalQuestions={attempt.questions.length}
                selectedOptionId={answers[currentQuestion.id] ?? null}
                saveStatus={saveStatuses[currentQuestion.id] ?? "idle"}
                onSelect={(optionId) => handleSelectOption(currentQuestion.id, optionId)}
                onClear={() => handleSelectOption(currentQuestion.id, null)}
              />
            )}

            <Stack direction="row" sx={{ justifyContent: "space-between" }}>
              <Button
                disabled={currentIndex === 0}
                onClick={() => setCurrentIndex((index) => Math.max(0, index - 1))}
              >
                Previous
              </Button>
              <Button
                component={RouterLink}
                to={ROUTES.student.quizzes}
                color="inherit"
                startIcon={<ArrowBackIcon />}
              >
                Back to quizzes
              </Button>
              <Button
                disabled={currentIndex === attempt.questions.length - 1}
                onClick={() =>
                  setCurrentIndex((index) => Math.min(attempt.questions.length - 1, index + 1))
                }
              >
                Next
              </Button>
            </Stack>
          </Stack>
        </Grid>
      </Grid>

      <SubmitAttemptDialog
        open={submitDialogOpen}
        unansweredCount={unansweredCount}
        isSubmitting={submitMutation.isPending}
        errorMessage={submitErrorMessage}
        onConfirm={handleSubmit}
        onClose={() => setSubmitDialogOpen(false)}
      />
    </Box>
  );
}

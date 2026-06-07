import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Link as RouterLink } from "react-router-dom";

import { AttemptAuditTimeline } from "../../components/admin/AttemptAuditTimeline";
import { SuspiciousnessChip } from "../../components/admin/SuspiciousnessChip";
import { StatCard } from "../../components/common/StatCard";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { ROUTES } from "../../constants/routes";
import { useAttemptAuditQuery } from "../../hooks/useAdminAttempts";
import { useQuizQuery } from "../../hooks/useQuizzes";
import {
  formatDateTime,
  formatScore,
  shortenId,
  STATUS_COLORS,
  statusLabel,
} from "../../utils/attemptFormatting";
import { calculateSuspiciousness } from "../../utils/suspiciousness";

export function AdminAttemptDetailPage() {
  const { attemptId = "" } = useParams<{ attemptId: string }>();
  const navigate = useNavigate();

  const auditQuery = useAttemptAuditQuery(attemptId);
  const attempt = auditQuery.data?.attempt;
  const quizQuery = useQuizQuery(attempt?.quiz_id ?? "");

  const suspiciousness = useMemo(() => {
    if (!auditQuery.data) return null;
    return calculateSuspiciousness(
      auditQuery.data.attempt.tab_switch_count,
      auditQuery.data.proctoring_events,
    );
  }, [auditQuery.data]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(ROUTES.admin.attempts)}
        >
          Back to Attempts
        </Button>
      </Stack>

      {auditQuery.isPending && <LoadingState message="Loading attempt..." />}

      {auditQuery.isError && (
        <ErrorState
          title="Failed to load attempt"
          message={auditQuery.error instanceof Error ? auditQuery.error.message : "Please try again."}
          onRetry={() => auditQuery.refetch()}
        />
      )}

      {auditQuery.data && attempt && (
        <>
          <Typography variant="h4">Attempt Details</Typography>

          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Metadata
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Student
                  </Typography>
                  <Typography variant="body1" sx={{ fontFamily: "monospace" }}>
                    {shortenId(attempt.student_id, 12)}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Quiz
                  </Typography>
                  {quizQuery.data ? (
                    <Typography
                      component={RouterLink}
                      to={ROUTES.admin.quizBuilder(attempt.quiz_id)}
                      variant="body1"
                      sx={{ textDecoration: "none" }}
                    >
                      {quizQuery.data.title}
                    </Typography>
                  ) : (
                    <Typography variant="body1" sx={{ fontFamily: "monospace" }}>
                      {shortenId(attempt.quiz_id, 12)}
                    </Typography>
                  )}
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    size="small"
                    label={statusLabel(attempt.status)}
                    color={STATUS_COLORS[attempt.status] ?? "default"}
                    variant="outlined"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Attempt Number
                  </Typography>
                  <Typography variant="body1">{attempt.attempt_number}</Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Started At
                  </Typography>
                  <Typography variant="body1">{formatDateTime(attempt.started_at)}</Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Submitted At
                  </Typography>
                  <Typography variant="body1">{formatDateTime(attempt.submitted_at)}</Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary">
                    Score
                  </Typography>
                  <Typography variant="body1">{formatScore(attempt.score)}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          <Box>
            <Typography variant="h6" gutterBottom>
              Anti-Cheat Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 4 }}>
                <StatCard label="Total Tab Switches" value={String(attempt.tab_switch_count)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <StatCard
                  label="Total Proctoring Events"
                  value={String(auditQuery.data.proctoring_events.length)}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 4 }}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      Suspiciousness
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      {suspiciousness && <SuspiciousnessChip level={suspiciousness} />}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>

          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Audit Timeline
              </Typography>
              <Divider sx={{ mb: 1 }} />
              <AttemptAuditTimeline
                attempt={attempt}
                tabSwitchLogs={auditQuery.data.tab_switch_logs}
                proctoringEvents={auditQuery.data.proctoring_events}
              />
            </CardContent>
          </Card>

          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Result Review
              </Typography>
              {attempt.score !== null ? (
                <Stack spacing={1}>
                  <Typography variant="body1">Score: {formatScore(attempt.score)}</Typography>
                  <Alert severity="info">
                    A detailed breakdown (percentage, correct/incorrect/unanswered) is only
                    available to the student via their own result view. The admin attempts API
                    exposes the raw score only.
                  </Alert>
                </Stack>
              ) : (
                <EmptyState
                  title="No result yet"
                  message="This attempt has not been finalized, so no score is available."
                />
              )}
            </CardContent>
          </Card>
        </>
      )}
    </Box>
  );
}

import {
  Box,
  Card,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
} from "@mui/material";

import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { StatCard } from "../../components/common/StatCard";
import { useAuth } from "../../context/AuthContext";
import { useStudentAnalyticsQuery, useStudentHistoryQuery } from "../../hooks/useAnalytics";
import { formatDateTime, formatScore, STATUS_COLORS, statusLabel } from "../../utils/attemptFormatting";

export function StudentDashboardPage() {
  const { user } = useAuth();
  const analyticsQuery = useStudentAnalyticsQuery();
  const historyQuery = useStudentHistoryQuery({ limit: 5 });

  const analytics = analyticsQuery.data;
  const recentAttempts = historyQuery.data?.items ?? [];

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="h4">Student Dashboard</Typography>

      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Welcome back, {user?.name}. Here's a snapshot of your quiz activity and recent
          attempts.
        </Typography>
      </Paper>

      {analyticsQuery.isPending && <LoadingState message="Loading your analytics..." />}

      {analyticsQuery.isError && (
        <ErrorState
          title="Failed to load your analytics"
          message={
            analyticsQuery.error instanceof Error
              ? analyticsQuery.error.message
              : "Please try again."
          }
          onRetry={() => analyticsQuery.refetch()}
        />
      )}

      {analytics && (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard label="Total attempts" value={String(analytics.total_attempts)} />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard label="Submitted attempts" value={String(analytics.submitted_count)} />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard label="Average score" value={formatScore(analytics.average_score)} />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <StatCard label="Best score" value={formatScore(analytics.best_score)} />
          </Grid>
        </Grid>
      )}

      <Box>
        <Typography variant="h6" gutterBottom>
          Recent attempts
        </Typography>

        {historyQuery.isPending && <LoadingState message="Loading recent attempts..." />}

        {historyQuery.isError && (
          <ErrorState
            title="Failed to load recent attempts"
            message={
              historyQuery.error instanceof Error
                ? historyQuery.error.message
                : "Please try again."
            }
            onRetry={() => historyQuery.refetch()}
          />
        )}

        {!historyQuery.isPending && !historyQuery.isError && recentAttempts.length === 0 && (
          <EmptyState
            title="No attempts yet"
            message="Once you start a quiz, your recent attempts will show up here."
          />
        )}

        {!historyQuery.isPending && !historyQuery.isError && recentAttempts.length > 0 && (
          <Card variant="outlined">
            <List disablePadding>
              {recentAttempts.map((attempt, index) => (
                <ListItem key={attempt.attempt_id} divider={index < recentAttempts.length - 1}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Typography variant="body1" component="span">
                          {attempt.quiz_title}
                        </Typography>
                        <Chip
                          size="small"
                          label={statusLabel(attempt.status)}
                          color={STATUS_COLORS[attempt.status] ?? "default"}
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Box component="span" sx={{ display: "flex", gap: 2, mt: 0.5 }}>
                        <Typography component="span" variant="caption" color="text.secondary">
                          Attempt #{attempt.attempt_number}
                        </Typography>
                        <Typography component="span" variant="caption" color="text.secondary">
                          Started: {formatDateTime(attempt.started_at)}
                        </Typography>
                        <Typography component="span" variant="caption" color="text.secondary">
                          Submitted: {formatDateTime(attempt.submitted_at)}
                        </Typography>
                        <Typography component="span" variant="caption" color="text.secondary">
                          Score: {formatScore(attempt.score)}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Card>
        )}
      </Box>
    </Box>
  );
}

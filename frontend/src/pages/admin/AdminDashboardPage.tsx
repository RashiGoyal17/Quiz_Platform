import { Box, Card, Chip, Grid, List, ListItem, ListItemText, Paper, Typography } from "@mui/material";

import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { StatCard } from "../../components/common/StatCard";
import { useAuth } from "../../context/AuthContext";
import { useAdminDashboardQuery } from "../../hooks/useAnalytics";
import {
  formatDateTime,
  formatScore,
  STATUS_COLORS,
  statusLabel,
} from "../../utils/attemptFormatting";

export function AdminDashboardPage() {
  const { user } = useAuth();
  const dashboardQuery = useAdminDashboardQuery();
  const dashboard = dashboardQuery.data;
  const recentAttempts = dashboard?.recent_attempts ?? [];

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="h4">Admin Dashboard</Typography>

      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Welcome back, {user?.name}. Here's a snapshot of platform activity, quiz usage, and
          anti-cheat metrics.
        </Typography>
      </Paper>

      {dashboardQuery.isPending && <LoadingState message="Loading dashboard metrics..." />}

      {dashboardQuery.isError && (
        <ErrorState
          title="Failed to load dashboard metrics"
          message={
            dashboardQuery.error instanceof Error
              ? dashboardQuery.error.message
              : "Please try again."
          }
          onRetry={() => dashboardQuery.refetch()}
        />
      )}

      {dashboard && (
        <>
          <Box>
            <Typography variant="h6" gutterBottom>
              Users
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Total users" value={String(dashboard.total_users)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Students" value={String(dashboard.total_students)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Admins" value={String(dashboard.total_admins)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Active users" value={String(dashboard.active_users)} />
              </Grid>
            </Grid>
          </Box>

          <Box>
            <Typography variant="h6" gutterBottom>
              Quizzes
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Total quizzes" value={String(dashboard.total_quizzes)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Published quizzes" value={String(dashboard.published_quizzes)} />
              </Grid>
            </Grid>
          </Box>

          <Box>
            <Typography variant="h6" gutterBottom>
              Attempts
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Total attempts" value={String(dashboard.total_attempts)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="In progress" value={String(dashboard.in_progress_attempts)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Submitted" value={String(dashboard.submitted_attempts)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Timed out" value={String(dashboard.timed_out_attempts)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                <StatCard label="Abandoned" value={String(dashboard.abandoned_attempts)} />
              </Grid>
            </Grid>
          </Box>

          <Box>
            <Typography variant="h6" gutterBottom>
              Anti-cheat
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                <StatCard label="Total tab switches" value={String(dashboard.total_tab_switches)} />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                <StatCard
                  label="Avg. tab switches / attempt"
                  value={formatScore(dashboard.average_tab_switches_per_attempt)}
                />
              </Grid>
              <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                <StatCard
                  label="Proctoring events"
                  value={String(dashboard.total_proctoring_events)}
                />
              </Grid>
            </Grid>
          </Box>
        </>
      )}

      <Box>
        <Typography variant="h6" gutterBottom>
          Recent activity
        </Typography>

        {dashboard && recentAttempts.length === 0 && (
          <EmptyState
            title="No recent activity"
            message="Attempts will appear here as students take quizzes."
          />
        )}

        {recentAttempts.length > 0 && (
          <Card variant="outlined">
            <List disablePadding>
              {recentAttempts.map((attempt, index) => (
                <ListItem key={attempt.attempt_id} divider={index < recentAttempts.length - 1}>
                  <ListItemText
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
                        <Typography variant="body1" component="span">
                          {attempt.student_username}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" component="span">
                          &middot; {attempt.quiz_title}
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
                      <Box component="span" sx={{ display: "flex", gap: 2, mt: 0.5, flexWrap: "wrap" }}>
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

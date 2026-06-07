import { useMemo, useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import BuildIcon from "@mui/icons-material/Build";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StopIcon from "@mui/icons-material/Stop";
import {
  Box,
  Button,
  Chip,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { PublishQuizDialog, type PublishQuizMode } from "../../components/admin/PublishQuizDialog";
import { QuizFormDialog, type QuizFormMode } from "../../components/admin/QuizFormDialog";
import { ROUTES } from "../../constants/routes";
import type { Quiz } from "../../api/types";
import {
  useCreateQuizMutation,
  usePublishQuizMutation,
  useQuizzesQuery,
  useUnpublishQuizMutation,
  useUpdateQuizMutation,
} from "../../hooks/useQuizzes";

type DialogState =
  | { kind: "create" }
  | { kind: "edit"; quiz: Quiz }
  | { kind: "publish"; quiz: Quiz }
  | { kind: "unpublish"; quiz: Quiz }
  | null;

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatDateTime(value: string | null): string {
  return value ? dateTimeFormatter.format(new Date(value)) : "—";
}

export function QuizzesPage() {
  const { data: quizzes, isPending, isError, error, refetch } = useQuizzesQuery();
  const navigate = useNavigate();

  const [dialog, setDialog] = useState<DialogState>(null);

  const createMutation = useCreateQuizMutation();
  const updateMutation = useUpdateQuizMutation();
  const publishMutation = usePublishQuizMutation();
  const unpublishMutation = useUnpublishQuizMutation();

  const closeDialog = () => {
    setDialog(null);
    createMutation.reset();
    updateMutation.reset();
    publishMutation.reset();
    unpublishMutation.reset();
  };

  const handleFormSubmit = (values: {
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
  }) => {
    const body = {
      title: values.title,
      description: values.description || null,
      duration_minutes: values.durationMinutes,
      start_time: values.startTime,
      end_time: values.endTime,
      shuffle_questions: values.shuffleQuestions,
      shuffle_options: values.shuffleOptions,
      max_attempts: values.maxAttempts,
      proctoring_enabled: values.proctoringEnabled,
      max_tab_switches: values.maxTabSwitches,
    };

    if (dialog?.kind === "create") {
      createMutation.mutate(body, { onSuccess: () => closeDialog() });
    } else if (dialog?.kind === "edit") {
      updateMutation.mutate({ id: dialog.quiz.id, body }, { onSuccess: () => closeDialog() });
    }
  };

  const handlePublishConfirm = () => {
    if (dialog?.kind === "publish") {
      publishMutation.mutate(dialog.quiz.id, { onSuccess: () => closeDialog() });
    } else if (dialog?.kind === "unpublish") {
      unpublishMutation.mutate(dialog.quiz.id, { onSuccess: () => closeDialog() });
    }
  };

  const columns = useMemo<GridColDef<Quiz>[]>(
    () => [
      {
        field: "title",
        headerName: "Title",
        flex: 1.4,
        minWidth: 220,
        renderCell: (params) => (
          <RouterLink
            to={ROUTES.admin.quizBuilder(params.row.id)}
            style={{ color: "inherit", textDecoration: "none", fontWeight: 500 }}
          >
            {params.row.title}
          </RouterLink>
        ),
      },
      {
        field: "duration_minutes",
        headerName: "Duration",
        width: 120,
        valueFormatter: (value: number) => `${value} min`,
      },
      {
        field: "is_published",
        headerName: "Published",
        width: 130,
        renderCell: (params) => (
          <Chip
            size="small"
            label={params.row.is_published ? "Published" : "Draft"}
            color={params.row.is_published ? "success" : "default"}
            variant={params.row.is_published ? "filled" : "outlined"}
          />
        ),
      },
      {
        field: "start_time",
        headerName: "Start time",
        width: 180,
        valueGetter: (_value, row) => formatDateTime(row.start_time),
      },
      {
        field: "end_time",
        headerName: "End time",
        width: 180,
        valueGetter: (_value, row) => formatDateTime(row.end_time),
      },
      {
        field: "max_attempts",
        headerName: "Max attempts",
        width: 130,
      },
      {
        field: "proctoring_enabled",
        headerName: "Proctoring",
        width: 120,
        renderCell: (params) => (
          <Chip
            size="small"
            label={params.row.proctoring_enabled ? "Enabled" : "Disabled"}
            color={params.row.proctoring_enabled ? "info" : "default"}
            variant={params.row.proctoring_enabled ? "filled" : "outlined"}
          />
        ),
      },
      {
        field: "actions",
        headerName: "Actions",
        width: 220,
        sortable: false,
        filterable: false,
        renderCell: (params) => (
          <Stack direction="row" spacing={0.5}>
            <Tooltip title="Open quiz builder">
              <IconButton
                size="small"
                aria-label={`Open builder for ${params.row.title}`}
                onClick={() => navigate(ROUTES.admin.quizBuilder(params.row.id))}
              >
                <BuildIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Edit metadata">
              <IconButton
                size="small"
                aria-label={`Edit ${params.row.title}`}
                onClick={() => setDialog({ kind: "edit", quiz: params.row })}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            {params.row.is_published ? (
              <Tooltip title="Unpublish">
                <IconButton
                  size="small"
                  aria-label={`Unpublish ${params.row.title}`}
                  onClick={() => setDialog({ kind: "unpublish", quiz: params.row })}
                >
                  <StopIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            ) : (
              <Tooltip title="Publish">
                <IconButton
                  size="small"
                  aria-label={`Publish ${params.row.title}`}
                  onClick={() => setDialog({ kind: "publish", quiz: params.row })}
                >
                  <PlayArrowIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title="Deleting quizzes isn't supported by the backend API yet">
              <span>
                <IconButton size="small" aria-label={`Delete ${params.row.title}`} disabled>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Stack>
        ),
      },
    ],
    [navigate],
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between" }}>
        <Typography variant="h4">Quizzes</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialog({ kind: "create" })}
        >
          Create quiz
        </Button>
      </Stack>

      {isPending && <LoadingState message="Loading quizzes..." />}

      {isError && (
        <ErrorState
          title="Failed to load quizzes"
          message={error instanceof Error ? error.message : "Please try again."}
          onRetry={() => refetch()}
        />
      )}

      {!isPending && !isError && quizzes && quizzes.length === 0 && (
        <EmptyState
          title="No quizzes yet"
          message="Create your first quiz to start assembling questions."
          action={
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDialog({ kind: "create" })}
            >
              Create quiz
            </Button>
          }
        />
      )}

      {!isPending && !isError && quizzes && quizzes.length > 0 && (
        <Box sx={{ height: 560 }}>
          <DataGrid
            rows={quizzes}
            columns={columns}
            getRowId={(row) => row.id}
            disableRowSelectionOnClick
            initialState={{
              pagination: { paginationModel: { pageSize: 10 } },
            }}
            pageSizeOptions={[10, 25, 50]}
          />
        </Box>
      )}

      <QuizFormDialog
        open={dialog?.kind === "create" || dialog?.kind === "edit"}
        mode={(dialog?.kind === "edit" ? "edit" : "create") as QuizFormMode}
        quiz={dialog?.kind === "edit" ? dialog.quiz : null}
        submitting={createMutation.isPending || updateMutation.isPending}
        error={dialog?.kind === "edit" ? updateMutation.error : createMutation.error}
        onClose={closeDialog}
        onSubmit={handleFormSubmit}
      />

      <PublishQuizDialog
        open={dialog?.kind === "publish" || dialog?.kind === "unpublish"}
        mode={(dialog?.kind === "unpublish" ? "unpublish" : "publish") as PublishQuizMode}
        quiz={dialog?.kind === "publish" || dialog?.kind === "unpublish" ? dialog.quiz : null}
        submitting={publishMutation.isPending || unpublishMutation.isPending}
        error={dialog?.kind === "unpublish" ? unpublishMutation.error : publishMutation.error}
        onClose={closeDialog}
        onConfirm={handlePublishConfirm}
      />
    </Box>
  );
}

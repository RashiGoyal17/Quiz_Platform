import { useMemo, useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { Box, Button, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";

import { DeleteQuestionDialog } from "../../components/admin/DeleteQuestionDialog";
import {
  QuestionFormDialog,
  type QuestionFormMode,
  type QuestionFormSubmitValues,
} from "../../components/admin/QuestionFormDialog";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import type { Question } from "../../api/types";
import { useQuestionBanksQuery } from "../../hooks/useQuestionBanks";
import {
  useAllQuestionsQuery,
  useCreateQuestionMutation,
  useDeleteQuestionMutation,
  useUpdateQuestionMutation,
} from "../../hooks/useQuestions";

type DialogState =
  | { kind: "create" }
  | { kind: "edit"; question: Question }
  | { kind: "delete"; question: Question }
  | null;

const dateFormatter = new Intl.DateTimeFormat(undefined, { dateStyle: "medium" });

const TEXT_PREVIEW_LENGTH = 80;

function previewText(text: string): string {
  return text.length > TEXT_PREVIEW_LENGTH ? `${text.slice(0, TEXT_PREVIEW_LENGTH)}…` : text;
}

export function QuestionsPage() {
  const banksQuery = useQuestionBanksQuery();
  const { data: questions, isPending, isError, error, refetch } = useAllQuestionsQuery();

  const [dialog, setDialog] = useState<DialogState>(null);

  const createMutation = useCreateQuestionMutation();
  const updateMutation = useUpdateQuestionMutation();
  const deleteMutation = useDeleteQuestionMutation();

  const banks = banksQuery.data ?? [];

  const closeDialog = () => {
    setDialog(null);
    createMutation.reset();
    updateMutation.reset();
    deleteMutation.reset();
  };

  const handleFormSubmit = (values: QuestionFormSubmitValues) => {
    const body = {
      text: values.text,
      explanation: values.explanation || null,
      marks: values.marks,
      negative_marks: values.negativeMarks,
      options: values.options,
    };

    if (dialog?.kind === "create") {
      createMutation.mutate({ bankId: values.bankId, body }, { onSuccess: () => closeDialog() });
    } else if (dialog?.kind === "edit") {
      updateMutation.mutate(
        { id: dialog.question.id, body },
        { onSuccess: () => closeDialog() },
      );
    }
  };

  const handleDeleteConfirm = () => {
    if (dialog?.kind === "delete") {
      deleteMutation.mutate(dialog.question.id, { onSuccess: () => closeDialog() });
    }
  };

  const columns = useMemo<GridColDef<Question>[]>(
    () => [
      {
        field: "text",
        headerName: "Question text",
        flex: 1.5,
        minWidth: 240,
        renderCell: (params) => (
          <Tooltip title={params.row.text}>
            <span>{previewText(params.row.text)}</span>
          </Tooltip>
        ),
      },
      {
        field: "questionBankName",
        headerName: "Question bank",
        flex: 1,
        minWidth: 160,
      },
      { field: "marks", headerName: "Marks", width: 100, type: "number" },
      {
        field: "negativeMarks",
        headerName: "Negative marks",
        width: 140,
        type: "number",
      },
      {
        field: "createdAt",
        headerName: "Created",
        width: 140,
        valueGetter: (_value, row) => new Date(row.createdAt),
        valueFormatter: (value: Date) => dateFormatter.format(value),
      },
      {
        field: "actions",
        headerName: "Actions",
        width: 120,
        sortable: false,
        filterable: false,
        renderCell: (params) => (
          <Stack direction="row" spacing={0.5}>
            <IconButton
              size="small"
              aria-label="Edit question"
              onClick={() => setDialog({ kind: "edit", question: params.row })}
            >
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              aria-label="Delete question"
              onClick={() => setDialog({ kind: "delete", question: params.row })}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Stack>
        ),
      },
    ],
    [],
  );

  const canCreate = banks.length > 0;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack
        direction="row"
        sx={{ alignItems: "center", justifyContent: "space-between" }}
      >
        <Typography variant="h4">Questions</Typography>
        <Tooltip title={canCreate ? "" : "Create a question bank first"}>
          <span>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              disabled={!canCreate}
              onClick={() => setDialog({ kind: "create" })}
            >
              Create question
            </Button>
          </span>
        </Tooltip>
      </Stack>

      {isPending && <LoadingState message="Loading questions..." />}

      {isError && (
        <ErrorState
          title="Failed to load questions"
          message={error instanceof Error ? error.message : "Please try again."}
          onRetry={() => refetch()}
        />
      )}

      {!isPending && !isError && questions && questions.length === 0 && (
        <EmptyState
          title="No questions yet"
          message={
            canCreate
              ? "Create your first question to start building quizzes."
              : "Create a question bank first, then add questions to it."
          }
          action={
            canCreate ? (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setDialog({ kind: "create" })}
              >
                Create question
              </Button>
            ) : undefined
          }
        />
      )}

      {!isPending && !isError && questions && questions.length > 0 && (
        <Box sx={{ height: 560 }}>
          <DataGrid
            rows={questions}
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

      <QuestionFormDialog
        open={dialog?.kind === "create" || dialog?.kind === "edit"}
        mode={(dialog?.kind === "edit" ? "edit" : "create") as QuestionFormMode}
        question={dialog?.kind === "edit" ? dialog.question : null}
        banks={banks}
        submitting={createMutation.isPending || updateMutation.isPending}
        error={dialog?.kind === "edit" ? updateMutation.error : createMutation.error}
        onClose={closeDialog}
        onSubmit={handleFormSubmit}
      />

      <DeleteQuestionDialog
        open={dialog?.kind === "delete"}
        question={dialog?.kind === "delete" ? dialog.question : null}
        submitting={deleteMutation.isPending}
        error={deleteMutation.error}
        onClose={closeDialog}
        onConfirm={handleDeleteConfirm}
      />
    </Box>
  );
}

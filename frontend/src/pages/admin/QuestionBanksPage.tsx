import { useMemo, useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import { Box, Button, IconButton, Stack, Typography } from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";

import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { DeleteQuestionBankDialog } from "../../components/admin/DeleteQuestionBankDialog";
import {
  QuestionBankFormDialog,
  type QuestionBankFormMode,
} from "../../components/admin/QuestionBankFormDialog";
import type { QuestionBank } from "../../api/types";
import {
  useCreateQuestionBankMutation,
  useDeleteQuestionBankMutation,
  useQuestionBanksQuery,
  useUpdateQuestionBankMutation,
} from "../../hooks/useQuestionBanks";

type DialogState =
  | { kind: "create" }
  | { kind: "edit"; bank: QuestionBank }
  | { kind: "delete"; bank: QuestionBank }
  | null;

const dateFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
});

export function QuestionBanksPage() {
  const { data: banks, isPending, isError, error, refetch } = useQuestionBanksQuery();

  const [dialog, setDialog] = useState<DialogState>(null);

  const createMutation = useCreateQuestionBankMutation();
  const updateMutation = useUpdateQuestionBankMutation();
  const deleteMutation = useDeleteQuestionBankMutation();

  const closeDialog = () => {
    setDialog(null);
    createMutation.reset();
    updateMutation.reset();
    deleteMutation.reset();
  };

  const handleFormSubmit = (values: { name: string; description: string }) => {
    const body = { name: values.name, description: values.description || null };

    if (dialog?.kind === "create") {
      createMutation.mutate(body, { onSuccess: () => closeDialog() });
    } else if (dialog?.kind === "edit") {
      updateMutation.mutate(
        { id: dialog.bank.id, body },
        { onSuccess: () => closeDialog() },
      );
    }
  };

  const handleDeleteConfirm = () => {
    if (dialog?.kind === "delete") {
      deleteMutation.mutate(dialog.bank.id, { onSuccess: () => closeDialog() });
    }
  };

  const columns = useMemo<GridColDef<QuestionBank>[]>(
    () => [
      { field: "name", headerName: "Name", flex: 1, minWidth: 180 },
      {
        field: "description",
        headerName: "Description",
        flex: 1.5,
        minWidth: 240,
        valueGetter: (_value, row) => row.description ?? "—",
      },
      {
        field: "created_at",
        headerName: "Created",
        width: 160,
        valueGetter: (_value, row) => new Date(row.created_at),
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
              aria-label={`Edit ${params.row.name}`}
              onClick={() => setDialog({ kind: "edit", bank: params.row })}
            >
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              aria-label={`Delete ${params.row.name}`}
              onClick={() => setDialog({ kind: "delete", bank: params.row })}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Stack>
        ),
      },
    ],
    [],
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Stack
        direction="row"
        sx={{ alignItems: "center", justifyContent: "space-between" }}
      >
        <Typography variant="h4">Question Banks</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialog({ kind: "create" })}
        >
          Create bank
        </Button>
      </Stack>

      {isPending && <LoadingState message="Loading question banks..." />}

      {isError && (
        <ErrorState
          title="Failed to load question banks"
          message={error instanceof Error ? error.message : "Please try again."}
          onRetry={() => refetch()}
        />
      )}

      {!isPending && !isError && banks && banks.length === 0 && (
        <EmptyState
          title="No question banks yet"
          message="Create your first question bank to start adding questions."
          action={
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDialog({ kind: "create" })}
            >
              Create bank
            </Button>
          }
        />
      )}

      {!isPending && !isError && banks && banks.length > 0 && (
        <Box sx={{ height: 520 }}>
          <DataGrid
            rows={banks}
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

      <QuestionBankFormDialog
        open={dialog?.kind === "create" || dialog?.kind === "edit"}
        mode={(dialog?.kind === "edit" ? "edit" : "create") as QuestionBankFormMode}
        bank={dialog?.kind === "edit" ? dialog.bank : null}
        submitting={createMutation.isPending || updateMutation.isPending}
        error={dialog?.kind === "edit" ? updateMutation.error : createMutation.error}
        onClose={closeDialog}
        onSubmit={handleFormSubmit}
      />

      <DeleteQuestionBankDialog
        open={dialog?.kind === "delete"}
        bank={dialog?.kind === "delete" ? dialog.bank : null}
        submitting={deleteMutation.isPending}
        error={deleteMutation.error}
        onClose={closeDialog}
        onConfirm={handleDeleteConfirm}
      />
    </Box>
  );
}

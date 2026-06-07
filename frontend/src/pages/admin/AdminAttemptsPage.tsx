import VisibilityIcon from "@mui/icons-material/Visibility";
import {
  Box,
  Button,
  Chip,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { AttemptAdminItem } from "../../api/types";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { ROUTES } from "../../constants/routes";
import { useAdminAttemptsQuery } from "../../hooks/useAdminAttempts";
import { useQuizzesQuery } from "../../hooks/useQuizzes";
import {
  formatDateTime,
  formatScore,
  shortenId,
  STATUS_COLORS,
  statusLabel,
} from "../../utils/attemptFormatting";

const PAGE_SIZE = 25;

const STATUS_FILTER_OPTIONS = [
  { value: "all", label: "All" },
  { value: "in_progress", label: "In Progress" },
  { value: "submitted", label: "Submitted" },
  { value: "timed_out", label: "Timed Out" },
  { value: "abandoned", label: "Abandoned" },
];

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function AdminAttemptsPage() {
  const navigate = useNavigate();
  const quizzesQuery = useQuizzesQuery();

  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState("all");
  const [quizFilter, setQuizFilter] = useState("all");
  const [studentIdInput, setStudentIdInput] = useState("");

  const trimmedStudentId = studentIdInput.trim();
  const studentIdValid = trimmedStudentId === "" || UUID_PATTERN.test(trimmedStudentId);
  const studentIdFilter = UUID_PATTERN.test(trimmedStudentId) ? trimmedStudentId : undefined;

  const attemptsQuery = useAdminAttemptsQuery({
    status: statusFilter === "all" ? undefined : statusFilter,
    quizId: quizFilter === "all" ? undefined : quizFilter,
    studentId: studentIdFilter,
    limit: PAGE_SIZE + 1,
    offset: page * PAGE_SIZE,
  });

  const items = attemptsQuery.data ?? [];
  const hasNextPage = items.length > PAGE_SIZE;
  const pageItems = items.slice(0, PAGE_SIZE);

  const quizTitleById = useMemo(() => {
    const map = new Map<string, string>();
    for (const quiz of quizzesQuery.data ?? []) {
      map.set(quiz.id, quiz.title);
    }
    return map;
  }, [quizzesQuery.data]);

  const resetPage = () => setPage(0);

  const handleStatusFilterChange = (event: SelectChangeEvent) => {
    setStatusFilter(event.target.value);
    resetPage();
  };

  const handleQuizFilterChange = (event: SelectChangeEvent) => {
    setQuizFilter(event.target.value);
    resetPage();
  };

  const handleStudentIdChange = (value: string) => {
    setStudentIdInput(value);
    resetPage();
  };

  const columns = useMemo<GridColDef<AttemptAdminItem>[]>(
    () => [
      {
        field: "student_id",
        headerName: "Student",
        width: 160,
        sortable: false,
        renderCell: (params) => (
          <Tooltip title={params.row.student_id}>
            <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
              {shortenId(params.row.student_id)}
            </Typography>
          </Tooltip>
        ),
      },
      {
        field: "quiz_id",
        headerName: "Quiz",
        flex: 1,
        minWidth: 180,
        sortable: false,
        renderCell: (params) => (
          <Tooltip title={params.row.quiz_id}>
            <Typography variant="body2">
              {quizTitleById.get(params.row.quiz_id) ?? shortenId(params.row.quiz_id)}
            </Typography>
          </Tooltip>
        ),
      },
      {
        field: "attempt_number",
        headerName: "Attempt #",
        width: 110,
        sortable: false,
      },
      {
        field: "status",
        headerName: "Status",
        width: 140,
        sortable: false,
        renderCell: (params) => (
          <Chip
            size="small"
            label={statusLabel(params.row.status)}
            color={STATUS_COLORS[params.row.status] ?? "default"}
            variant="outlined"
          />
        ),
      },
      {
        field: "score",
        headerName: "Score",
        width: 100,
        sortable: false,
        valueGetter: (_value, row) => formatScore(row.score),
      },
      {
        field: "started_at",
        headerName: "Started At",
        width: 180,
        sortable: false,
        valueGetter: (_value, row) => formatDateTime(row.started_at),
      },
      {
        field: "submitted_at",
        headerName: "Submitted At",
        width: 180,
        sortable: false,
        valueGetter: (_value, row) => formatDateTime(row.submitted_at),
      },
      {
        field: "tab_switch_count",
        headerName: "Tab Switches",
        width: 130,
        sortable: false,
      },
      {
        field: "actions",
        headerName: "Actions",
        width: 100,
        sortable: false,
        filterable: false,
        renderCell: (params) => (
          <Tooltip title="View attempt details">
            <IconButton
              size="small"
              aria-label={`View attempt ${params.row.id}`}
              onClick={() => navigate(ROUTES.admin.attemptDetail(params.row.id))}
            >
              <VisibilityIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        ),
      },
    ],
    [navigate, quizTitleById],
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Typography variant="h4">Attempts</Typography>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} sx={{ flexWrap: "wrap" }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel id="attempts-status-filter-label">Status</InputLabel>
          <Select
            labelId="attempts-status-filter-label"
            label="Status"
            value={statusFilter}
            onChange={handleStatusFilterChange}
          >
            {STATUS_FILTER_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel id="attempts-quiz-filter-label">Quiz</InputLabel>
          <Select
            labelId="attempts-quiz-filter-label"
            label="Quiz"
            value={quizFilter}
            onChange={handleQuizFilterChange}
          >
            <MenuItem value="all">All quizzes</MenuItem>
            {(quizzesQuery.data ?? []).map((quiz) => (
              <MenuItem key={quiz.id} value={quiz.id}>
                {quiz.title}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          label="Student ID (UUID)"
          placeholder="Paste a student id…"
          value={studentIdInput}
          onChange={(event) => handleStudentIdChange(event.target.value)}
          error={!studentIdValid}
          helperText={!studentIdValid ? "Enter a valid UUID or clear this field" : " "}
          size="small"
          sx={{ minWidth: 260 }}
        />
      </Stack>

      {attemptsQuery.isPending && <LoadingState message="Loading attempts..." />}

      {attemptsQuery.isError && (
        <ErrorState
          title="Failed to load attempts"
          message={
            attemptsQuery.error instanceof Error ? attemptsQuery.error.message : "Please try again."
          }
          onRetry={() => attemptsQuery.refetch()}
        />
      )}

      {!attemptsQuery.isPending && !attemptsQuery.isError && pageItems.length === 0 && (
        <EmptyState
          title="No attempts found"
          message="Try adjusting your filters."
        />
      )}

      {pageItems.length > 0 && (
        <>
          <Box sx={{ height: 600 }}>
            <DataGrid
              rows={pageItems}
              columns={columns}
              getRowId={(row) => row.id}
              disableRowSelectionOnClick
              hideFooter
            />
          </Box>
          <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "flex-end" }}>
            <Typography variant="body2" color="text.secondary">
              Page {page + 1}
            </Typography>
            <Button disabled={page === 0} onClick={() => setPage((value) => Math.max(0, value - 1))}>
              Previous
            </Button>
            <Button disabled={!hasNextPage} onClick={() => setPage((value) => value + 1)}>
              Next
            </Button>
          </Stack>
        </>
      )}
    </Box>
  );
}

import SearchIcon from "@mui/icons-material/Search";
import {
  Box,
  Button,
  Card,
  Chip,
  FormControl,
  InputAdornment,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Pagination,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material";
import { useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { ROUTES } from "../../constants/routes";
import { useStudentHistoryQuery } from "../../hooks/useAnalytics";
import {
  formatDateTime,
  formatScore,
  STATUS_COLORS,
  statusLabel,
} from "../../utils/attemptFormatting";

const FETCH_LIMIT = 100;
const PAGE_SIZE = 10;

type StatusFilter = "all" | "in_progress" | "submitted" | "timed_out" | "abandoned";

const STATUS_FILTER_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "in_progress", label: "In Progress" },
  { value: "submitted", label: "Submitted" },
  { value: "timed_out", label: "Timed Out" },
  { value: "abandoned", label: "Abandoned" },
];

export function ResultsPage() {
  const historyQuery = useStudentHistoryQuery({ limit: FETCH_LIMIT, offset: 0 });
  const items = useMemo(() => historyQuery.data?.items ?? [], [historyQuery.data]);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    return items.filter((item) => {
      const matchesSearch = !query || item.quiz_title.toLowerCase().includes(query);
      const matchesStatus = statusFilter === "all" || item.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [items, search, statusFilter]);

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const handleStatusFilterChange = (value: StatusFilter) => {
    setStatusFilter(value);
    setPage(1);
  };

  const pageCount = Math.max(1, Math.ceil(filteredItems.length / PAGE_SIZE));
  const pagedItems = filteredItems.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="h4">Results</Typography>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField
          label="Search by quiz title"
          value={search}
          onChange={(event) => handleSearchChange(event.target.value)}
          size="small"
          fullWidth
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            },
          }}
        />
        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel id="results-status-filter-label">Status</InputLabel>
          <Select
            labelId="results-status-filter-label"
            label="Status"
            value={statusFilter}
            onChange={(event: SelectChangeEvent) => handleStatusFilterChange(event.target.value as StatusFilter)}
          >
            {STATUS_FILTER_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      {historyQuery.isPending && <LoadingState message="Loading your attempts..." />}

      {historyQuery.isError && (
        <ErrorState
          title="Failed to load your attempts"
          message={
            historyQuery.error instanceof Error ? historyQuery.error.message : "Please try again."
          }
          onRetry={() => historyQuery.refetch()}
        />
      )}

      {!historyQuery.isPending && !historyQuery.isError && items.length === 0 && (
        <EmptyState
          title="No attempts yet"
          message="Once you start a quiz, your attempts will show up here."
        />
      )}

      {!historyQuery.isPending &&
        !historyQuery.isError &&
        items.length > 0 &&
        filteredItems.length === 0 && (
          <EmptyState
            title="No matching attempts"
            message="Try adjusting your search or status filter."
          />
        )}

      {pagedItems.length > 0 && (
        <Card variant="outlined">
          <List disablePadding>
            {pagedItems.map((attempt, index) => {
              const isInProgress = attempt.status === "in_progress";
              return (
                <ListItem
                  key={attempt.attempt_id}
                  divider={index < pagedItems.length - 1}
                  secondaryAction={
                    isInProgress ? (
                      <Button
                        component={RouterLink}
                        to={ROUTES.student.attemptDetail(attempt.attempt_id, attempt.quiz_id)}
                        variant="outlined"
                        size="small"
                      >
                        Resume
                      </Button>
                    ) : (
                      <Button
                        component={RouterLink}
                        to={ROUTES.student.attemptResult(attempt.attempt_id)}
                        variant="outlined"
                        size="small"
                      >
                        View result
                      </Button>
                    )
                  }
                >
                  <ListItemText
                    sx={{ pr: 14 }}
                    primary={
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
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
                      <Box component="span" sx={{ display: "flex", gap: 2, mt: 0.5, flexWrap: "wrap" }}>
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
              );
            })}
          </List>
        </Card>
      )}

      {filteredItems.length > PAGE_SIZE && (
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <Pagination
            count={pageCount}
            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
          />
        </Box>
      )}
    </Box>
  );
}

import { useRef, useState } from "react";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { isAxiosError } from "axios";

import type { ImportFormat } from "../../api/questionApi";
import type { ApiErrorResponse, BulkImportResponse, QuestionBank } from "../../api/types";

interface ImportQuestionsDialogProps {
  open: boolean;
  banks: QuestionBank[];
  submitting: boolean;
  result: BulkImportResponse | null;
  error: unknown;
  onClose: () => void;
  onSubmit: (bankId: string, file: File, format: ImportFormat) => void;
}

export function ImportQuestionsDialog({
  open,
  banks,
  submitting,
  result,
  error,
  onClose,
  onSubmit,
}: ImportQuestionsDialogProps) {
  const [bankId, setBankId] = useState<string>(banks[0]?.id ?? "");
  const [format, setFormat] = useState<ImportFormat>("csv");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const accepted = format === "csv" ? ".csv" : ".json";

  const handleFile = (f: File) => {
    setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  };

  const handleSubmit = () => {
    if (!file || !bankId) return;
    onSubmit(bankId, file, format);
  };

  const axiosDetail = isAxiosError<ApiErrorResponse>(error)
    ? error.response?.data?.detail
    : null;
  const networkError = error
    ? axiosDetail ?? (error instanceof Error ? error.message : "Something went wrong")
    : null;

  const hasResult = result !== null;
  const allFailed = hasResult && result.imported === 0 && result.failed > 0;
  const allPassed = hasResult && result.failed === 0 && result.imported > 0;
  const partial = hasResult && result.imported > 0 && result.failed > 0;

  return (
    <Dialog open={open} onClose={submitting ? undefined : onClose} fullWidth maxWidth="sm">
      <DialogTitle>Import questions</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2.5, pt: 2 }}>
        {networkError && <Alert severity="error">{networkError}</Alert>}

        {hasResult && (
          <Alert severity={allFailed ? "error" : partial ? "warning" : "success"}>
            {allPassed && `All ${result.imported} question(s) imported successfully.`}
            {partial && `${result.imported} imported, ${result.failed} failed — see errors below.`}
            {allFailed && `Import failed: all ${result.failed} row(s) had errors.`}
          </Alert>
        )}

        <FormControl fullWidth required disabled={submitting || hasResult}>
          <InputLabel id="import-bank-label">Question bank</InputLabel>
          <Select
            labelId="import-bank-label"
            label="Question bank"
            value={bankId}
            onChange={(e) => setBankId(e.target.value)}
          >
            {banks.map((b) => (
              <MenuItem key={b.id} value={b.id}>
                {b.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Format
          </Typography>
          <ToggleButtonGroup
            exclusive
            value={format}
            onChange={(_, v) => { if (v) setFormat(v as ImportFormat); }}
            size="small"
            disabled={submitting || hasResult}
          >
            <ToggleButton value="csv">CSV</ToggleButton>
            <ToggleButton value="json">JSON</ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => { if (!submitting && !hasResult) inputRef.current?.click(); }}
          sx={{
            border: "2px dashed",
            borderColor: dragOver ? "primary.main" : "divider",
            borderRadius: 2,
            p: 3,
            textAlign: "center",
            cursor: submitting || hasResult ? "default" : "pointer",
            bgcolor: dragOver ? "action.hover" : "background.paper",
            transition: "border-color 0.15s, background 0.15s",
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={accepted}
            style={{ display: "none" }}
            onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
            disabled={submitting || hasResult}
          />
          <Stack spacing={1} alignItems="center">
            <UploadFileIcon sx={{ fontSize: 40, color: "text.secondary" }} />
            {file ? (
              <Chip label={file.name} onDelete={() => setFile(null)} />
            ) : (
              <Typography variant="body2" color="text.secondary">
                Drag &amp; drop a {format.toUpperCase()} file here, or click to browse
              </Typography>
            )}
          </Stack>
        </Box>

        {format === "csv" && !hasResult && (
          <Box>
            <Typography variant="caption" color="text.secondary" component="div">
              Expected CSV columns:{" "}
              <code>text, explanation, marks, negative_marks, option_a, option_b, option_c, option_d, correct_option</code>
              <br />
              <code>correct_option</code> must be <code>A</code>, <code>B</code>, <code>C</code>, or <code>D</code>.
            </Typography>
          </Box>
        )}

        {hasResult && result.errors.length > 0 && (
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Row errors ({result.errors.length})
            </Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 240 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell width={60}>Row</TableCell>
                    <TableCell width={120}>Field</TableCell>
                    <TableCell>Message</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.errors.map((err, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{err.row}</TableCell>
                      <TableCell>{err.field ?? "—"}</TableCell>
                      <TableCell>{err.message}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={submitting}>
          {hasResult ? "Close" : "Cancel"}
        </Button>
        {!hasResult && (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!file || !bankId || submitting}
          >
            {submitting ? "Importing…" : "Import"}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}

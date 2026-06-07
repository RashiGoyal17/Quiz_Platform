import { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { isAxiosError } from "axios";

import type { ApiErrorResponse } from "../../api/types";
import { useAllQuestionsQuery } from "../../hooks/useQuestions";
import { useQuestionBanksQuery } from "../../hooks/useQuestionBanks";
import { useAddQuestionToQuizMutation } from "../../hooks/useQuizQuestions";

interface QuestionPickerDialogProps {
  open: boolean;
  quizId: string;
  assignedQuestionIds: ReadonlySet<string>;
  nextPosition: number;
  onClose: () => void;
}

const ALL_BANKS = "all";
const PREVIEW_LENGTH = 140;

function previewText(text: string): string {
  return text.length > PREVIEW_LENGTH ? `${text.slice(0, PREVIEW_LENGTH)}…` : text;
}

export function QuestionPickerDialog({
  open,
  quizId,
  assignedQuestionIds,
  nextPosition,
  onClose,
}: QuestionPickerDialogProps) {
  const [bankId, setBankId] = useState<string>(ALL_BANKS);
  const [search, setSearch] = useState("");
  const [addingQuestionId, setAddingQuestionId] = useState<string | null>(null);

  const banksQuery = useQuestionBanksQuery();
  const questionsQuery = useAllQuestionsQuery();
  const addMutation = useAddQuestionToQuizMutation();

  const banks = banksQuery.data ?? [];

  const candidates = useMemo(() => {
    const questions = questionsQuery.data ?? [];
    const trimmedSearch = search.trim().toLowerCase();
    return questions.filter((question) => {
      if (assignedQuestionIds.has(question.id)) return false;
      if (bankId !== ALL_BANKS && question.questionBankId !== bankId) return false;
      if (trimmedSearch && !question.text.toLowerCase().includes(trimmedSearch)) return false;
      return true;
    });
  }, [questionsQuery.data, assignedQuestionIds, bankId, search]);

  const handleAdd = (questionId: string) => {
    setAddingQuestionId(questionId);
    addMutation.mutate(
      { quizId, body: { question_id: questionId, position: nextPosition } },
      { onSettled: () => setAddingQuestionId(null) },
    );
  };

  const handleClose = () => {
    setBankId(ALL_BANKS);
    setSearch("");
    addMutation.reset();
    onClose();
  };

  const errorMessage = isAxiosError<ApiErrorResponse>(addMutation.error)
    ? addMutation.error.response?.data?.detail
    : undefined;

  return (
    <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
      <DialogTitle>Add questions to quiz</DialogTitle>
      <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {addMutation.isError && (
          <Alert severity="error">
            {errorMessage ?? "Unable to add this question. Please try again."}
          </Alert>
        )}

        <Stack direction="row" spacing={2}>
          <TextField
            select
            label="Question bank"
            value={bankId}
            onChange={(e) => setBankId(e.target.value)}
            sx={{ minWidth: 200 }}
          >
            <MenuItem value={ALL_BANKS}>All banks</MenuItem>
            {banks.map((bank) => (
              <MenuItem key={bank.id} value={bank.id}>
                {bank.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Search question text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            fullWidth
          />
        </Stack>

        {questionsQuery.isPending || banksQuery.isPending ? (
          <Typography color="text.secondary">Loading questions...</Typography>
        ) : candidates.length === 0 ? (
          <Typography color="text.secondary">
            No matching questions available to add.
          </Typography>
        ) : (
          <List sx={{ maxHeight: 360, overflowY: "auto" }}>
            {candidates.map((question) => (
              <ListItem
                key={question.id}
                divider
                secondaryAction={
                  <IconButton
                    edge="end"
                    color="primary"
                    aria-label={`Add question to quiz`}
                    disabled={addMutation.isPending}
                    onClick={() => handleAdd(question.id)}
                  >
                    <AddIcon />
                  </IconButton>
                }
              >
                <ListItemText
                  primary={previewText(question.text)}
                  secondary={
                    <Box component="span" sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                      <Chip size="small" label={question.questionBankName} />
                      <Typography component="span" variant="caption" color="text.secondary">
                        {question.marks} marks
                        {addingQuestionId === question.id && addMutation.isPending
                          ? " · Adding..."
                          : ""}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose}>Done</Button>
      </DialogActions>
    </Dialog>
  );
}

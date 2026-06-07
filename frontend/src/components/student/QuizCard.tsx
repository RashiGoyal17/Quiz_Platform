import AccessTimeIcon from "@mui/icons-material/AccessTime";
import EventIcon from "@mui/icons-material/Event";
import RepeatIcon from "@mui/icons-material/Repeat";
import VisibilityIcon from "@mui/icons-material/Visibility";
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";

import type { QuizAvailable } from "../../api/types";

interface QuizCardProps {
  quiz: QuizAvailable;
  onStart: (quiz: QuizAvailable) => void;
}

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatDateTime(value: string | null): string {
  return value ? dateTimeFormatter.format(new Date(value)) : "No restriction";
}

export function QuizCard({ quiz, onStart }: QuizCardProps) {
  return (
    <Card variant="outlined" sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <CardContent sx={{ flexGrow: 1, display: "flex", flexDirection: "column", gap: 1.5 }}>
        <Typography variant="h6">{quiz.title}</Typography>
        <Typography variant="body2" color="text.secondary">
          {quiz.description ?? "No description provided."}
        </Typography>

        <Stack spacing={0.75} sx={{ mt: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <AccessTimeIcon fontSize="small" color="action" />
            <Typography variant="body2">{quiz.duration_minutes} minutes</Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <EventIcon fontSize="small" color="action" />
            <Typography variant="body2">
              Starts: {formatDateTime(quiz.start_time)}
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <EventIcon fontSize="small" color="action" />
            <Typography variant="body2">Ends: {formatDateTime(quiz.end_time)}</Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <RepeatIcon fontSize="small" color="action" />
            <Typography variant="body2">Max attempts: {quiz.max_attempts}</Typography>
          </Box>
        </Stack>

        {quiz.proctoring_enabled && (
          <Tooltip title="This quiz is monitored — tab switches and other activity may be recorded.">
            <Chip
              size="small"
              icon={<VisibilityIcon />}
              label="Proctoring enabled"
              color="info"
              variant="outlined"
              sx={{ alignSelf: "flex-start" }}
            />
          </Tooltip>
        )}
      </CardContent>
      <CardActions sx={{ px: 2, pb: 2 }}>
        <Button variant="contained" fullWidth onClick={() => onStart(quiz)}>
          Start Quiz
        </Button>
      </CardActions>
    </Card>
  );
}

import { useState } from "react";
import { Box, Grid, Typography } from "@mui/material";

import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";
import { QuizCard } from "../../components/student/QuizCard";
import { StartQuizDialog } from "../../components/student/StartQuizDialog";
import type { QuizAvailable } from "../../api/types";
import { useAvailableQuizzesQuery } from "../../hooks/useQuizzes";

export function AvailableQuizzesPage() {
  const { data: quizzes, isPending, isError, error, refetch } = useAvailableQuizzesQuery();
  const [selectedQuiz, setSelectedQuiz] = useState<QuizAvailable | null>(null);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Typography variant="h4">Available Quizzes</Typography>

      {isPending && <LoadingState message="Loading available quizzes..." />}

      {isError && (
        <ErrorState
          title="Failed to load available quizzes"
          message={error instanceof Error ? error.message : "Please try again."}
          onRetry={() => refetch()}
        />
      )}

      {!isPending && !isError && quizzes && quizzes.length === 0 && (
        <EmptyState
          title="No quizzes available right now"
          message="Check back later — quizzes will appear here once they open for attempts."
        />
      )}

      {!isPending && !isError && quizzes && quizzes.length > 0 && (
        <Grid container spacing={2}>
          {quizzes.map((quiz) => (
            <Grid key={quiz.id} size={{ xs: 12, sm: 6, md: 4 }}>
              <QuizCard quiz={quiz} onStart={setSelectedQuiz} />
            </Grid>
          ))}
        </Grid>
      )}

      <StartQuizDialog
        open={selectedQuiz !== null}
        quiz={selectedQuiz}
        onClose={() => setSelectedQuiz(null)}
      />
    </Box>
  );
}

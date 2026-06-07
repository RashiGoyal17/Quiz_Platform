import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { quizApi } from "../api/quizApi";
import type { AddQuestionToQuizRequest, QuizQuestion } from "../api/types";
import { quizQueryKey, quizzesQueryKey } from "./useQuizzes";

export function quizQuestionsQueryKey(quizId: string) {
  return ["quiz-questions", quizId] as const;
}

export function useQuizQuestionsQuery(quizId: string) {
  return useQuery({
    queryKey: quizQuestionsQueryKey(quizId),
    queryFn: () => quizApi.listQuizQuestions(quizId),
    enabled: Boolean(quizId),
  });
}

function invalidateQuizQuestionState(
  queryClient: ReturnType<typeof useQueryClient>,
  quizId: string,
) {
  queryClient.invalidateQueries({ queryKey: quizQuestionsQueryKey(quizId) });
  // Question count affects publish-readiness, surfaced on both the list and the builder.
  queryClient.invalidateQueries({ queryKey: quizzesQueryKey });
  queryClient.invalidateQueries({ queryKey: quizQueryKey(quizId) });
}

export function useAddQuestionToQuizMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ quizId, body }: { quizId: string; body: AddQuestionToQuizRequest }) =>
      quizApi.addQuestionToQuiz(quizId, body),
    onSuccess: (_data, variables) => {
      invalidateQuizQuestionState(queryClient, variables.quizId);
    },
  });
}

export function useRemoveQuestionFromQuizMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ quizId, questionId }: { quizId: string; questionId: string }) =>
      quizApi.removeQuestionFromQuiz(quizId, questionId),
    onSuccess: (_data, variables) => {
      invalidateQuizQuestionState(queryClient, variables.quizId);
    },
  });
}

interface MoveVariables {
  quizId: string;
  first: QuizQuestion;
  second: QuizQuestion;
}

/**
 * Swaps the positions of two adjacent quiz questions.
 *
 * TECH DEBT: the backend has no update/reorder endpoint for quiz_questions —
 * `quizzes_router` only supports assigning (`POST .../questions`, which rejects
 * duplicates) and unassigning (`DELETE .../questions/{question_id}`); there is
 * no `PATCH` for `position` (confirmed via QuizService/QuizRepository — only
 * `add_question`/`remove_question` exist). Reordering is therefore emulated by
 * removing both rows and re-adding them with swapped positions, preserving each
 * one's `marks_override`. This is not atomic (a brief window exists where the
 * questions are unassigned) and costs 4 requests per swap. A dedicated
 * `PATCH /quizzes/{id}/questions/{question_id}` or bulk-reorder endpoint on the
 * backend would let this be replaced with a single call.
 */
export function useMoveQuizQuestionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ quizId, first, second }: MoveVariables) => {
      await quizApi.removeQuestionFromQuiz(quizId, first.question_id);
      await quizApi.removeQuestionFromQuiz(quizId, second.question_id);
      await quizApi.addQuestionToQuiz(quizId, {
        question_id: second.question_id,
        position: first.position,
        marks_override: second.marks_override,
      });
      await quizApi.addQuestionToQuiz(quizId, {
        question_id: first.question_id,
        position: second.position,
        marks_override: first.marks_override,
      });
    },
    onSuccess: (_data, variables) => {
      invalidateQuizQuestionState(queryClient, variables.quizId);
    },
  });
}

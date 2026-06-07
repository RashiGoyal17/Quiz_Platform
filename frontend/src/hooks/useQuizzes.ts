import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { quizApi } from "../api/quizApi";
import type { QuizCreateRequest, QuizUpdateRequest } from "../api/types";

export const quizzesQueryKey = ["quizzes"] as const;

export function quizQueryKey(id: string) {
  return [...quizzesQueryKey, id] as const;
}

export function useQuizzesQuery() {
  return useQuery({
    queryKey: quizzesQueryKey,
    queryFn: quizApi.list,
  });
}

export const availableQuizzesQueryKey = ["quizzes", "available"] as const;

export function useAvailableQuizzesQuery() {
  return useQuery({
    queryKey: availableQuizzesQueryKey,
    queryFn: quizApi.available,
  });
}

export function useQuizQuery(id: string) {
  return useQuery({
    queryKey: quizQueryKey(id),
    queryFn: () => quizApi.getById(id),
    enabled: Boolean(id),
  });
}

export function useCreateQuizMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: QuizCreateRequest) => quizApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: quizzesQueryKey });
    },
  });
}

export function useUpdateQuizMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: QuizUpdateRequest }) =>
      quizApi.update(id, body),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: quizzesQueryKey });
      queryClient.invalidateQueries({ queryKey: quizQueryKey(variables.id) });
    },
  });
}

export function usePublishQuizMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => quizApi.publish(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: quizzesQueryKey });
      queryClient.invalidateQueries({ queryKey: quizQueryKey(id) });
    },
  });
}

export function useUnpublishQuizMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => quizApi.unpublish(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: quizzesQueryKey });
      queryClient.invalidateQueries({ queryKey: quizQueryKey(id) });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { questionBankApi } from "../api/questionBankApi";
import type { QuestionBankCreateRequest, QuestionBankUpdateRequest } from "../api/types";

export const questionBanksQueryKey = ["question-banks"] as const;

export function useQuestionBanksQuery() {
  return useQuery({
    queryKey: questionBanksQueryKey,
    queryFn: questionBankApi.list,
  });
}

export function useCreateQuestionBankMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: QuestionBankCreateRequest) => questionBankApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionBanksQueryKey });
    },
  });
}

export function useUpdateQuestionBankMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: QuestionBankUpdateRequest }) =>
      questionBankApi.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionBanksQueryKey });
    },
  });
}

export function useDeleteQuestionBankMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => questionBankApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionBanksQueryKey });
    },
  });
}

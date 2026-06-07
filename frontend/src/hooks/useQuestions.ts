import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";

import { questionApi, type ImportFormat } from "../api/questionApi";
import type {
  BulkImportResponse,
  Question,
  QuestionCreateRequest,
  QuestionRecord,
  QuestionUpdateRequest,
} from "../api/types";
import { useQuestionBanksQuery } from "./useQuestionBanks";

export const questionsQueryKey = ["questions"] as const;

function questionsByBankQueryKey(bankId: string) {
  return [...questionsQueryKey, bankId] as const;
}

function normalizeQuestion(record: QuestionRecord, questionBankName: string): Question {
  return {
    id: record.id,
    text: record.text,
    explanation: record.explanation,
    questionBankId: record.question_bank_id,
    questionBankName,
    marks: record.marks,
    negativeMarks: record.negative_marks,
    options: record.options,
    createdAt: record.created_at,
  };
}

/**
 * Aggregates questions across every question bank into a single flat list.
 *
 * TECH DEBT: the backend exposes no global "list all questions" endpoint —
 * questions can only be listed per bank via `GET /question-banks/{id}/questions`
 * (confirmed: `questions_router` only has `/questions/{id}` get/put/delete routes,
 * no collection route). This hook fans out one request per bank with `useQueries`
 * and flattens the results client-side — an N+1 pattern that scales linearly with
 * the number of question banks. Each per-bank list is still cached/invalidated
 * independently, so this is acceptable at the expected admin scale, but if the
 * number of banks grows large a backend aggregate/paginated endpoint should
 * replace this.
 */
export function useAllQuestionsQuery() {
  const banksQuery = useQuestionBanksQuery();
  const banks = banksQuery.data ?? [];

  const questionQueries = useQueries({
    queries: banks.map((bank) => ({
      queryKey: questionsByBankQueryKey(bank.id),
      queryFn: () => questionApi.listByBank(bank.id),
      enabled: banksQuery.isSuccess,
    })),
  });

  const isPending = banksQuery.isPending || questionQueries.some((q) => q.isPending);
  const isError = banksQuery.isError || questionQueries.some((q) => q.isError);
  const error = banksQuery.error ?? questionQueries.find((q) => q.error)?.error ?? null;

  const data: Question[] | undefined =
    banksQuery.isSuccess && questionQueries.every((q) => q.isSuccess)
      ? banks.flatMap((bank, index) =>
          (questionQueries[index].data ?? []).map((record) =>
            normalizeQuestion(record, bank.name),
          ),
        )
      : undefined;

  const refetch = () => {
    void banksQuery.refetch();
    questionQueries.forEach((q) => void q.refetch());
  };

  return { data, isPending, isError, error, refetch };
}

export function useCreateQuestionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bankId, body }: { bankId: string; body: QuestionCreateRequest }) =>
      questionApi.create(bankId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionsQueryKey });
    },
  });
}

export function useUpdateQuestionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: QuestionUpdateRequest }) =>
      questionApi.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionsQueryKey });
    },
  });
}

export function useDeleteQuestionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => questionApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: questionsQueryKey });
    },
  });
}

export function useImportQuestionsMutation() {
  const queryClient = useQueryClient();
  return useMutation<
    BulkImportResponse,
    Error,
    { bankId: string; file: File; format: ImportFormat }
  >({
    mutationFn: ({ bankId, file, format }) =>
      questionApi.importFromFile(bankId, file, format),
    onSuccess: (data) => {
      if (data.imported > 0) {
        queryClient.invalidateQueries({ queryKey: questionsQueryKey });
      }
    },
  });
}

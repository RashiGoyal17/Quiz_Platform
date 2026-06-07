import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { attemptApi } from "../api/attemptApi";
import type {
  ProctoringEventRequest,
  SaveAnswerRequest,
  StartAttemptRequest,
} from "../api/types";

export function useStartAttemptMutation() {
  return useMutation({
    mutationFn: (body: StartAttemptRequest) => attemptApi.start(body),
  });
}

export function attemptQueryKey(attemptId: string, quizId: string | null) {
  return ["attempts", attemptId, quizId] as const;
}

/**
 * Loads (and resumes) an in-progress attempt. There is no GET /attempts/{id}
 * endpoint — POST /attempts/start is idempotent and returns the existing
 * IN_PROGRESS attempt when one exists, so it doubles as the resume path.
 * Requires quizId (carried via the URL query string) since the start
 * endpoint needs it.
 */
export function useAttemptQuery(attemptId: string, quizId: string | null) {
  return useQuery({
    queryKey: attemptQueryKey(attemptId, quizId),
    queryFn: () => attemptApi.start({ quiz_id: quizId as string }),
    enabled: Boolean(attemptId) && Boolean(quizId),
    retry: false,
    refetchOnWindowFocus: false,
  });
}

export function attemptResultQueryKey(attemptId: string) {
  return ["attempts", attemptId, "result"] as const;
}

export function useAttemptResultQuery(attemptId: string, enabled = true) {
  return useQuery({
    queryKey: attemptResultQueryKey(attemptId),
    queryFn: () => attemptApi.getResult(attemptId),
    enabled: Boolean(attemptId) && enabled,
    retry: false,
    refetchOnWindowFocus: false,
  });
}

export function useSaveAnswerMutation(attemptId: string) {
  return useMutation({
    mutationFn: (body: SaveAnswerRequest) => attemptApi.saveAnswer(attemptId, body),
  });
}

export function useSubmitAttemptMutation(attemptId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => attemptApi.submit(attemptId),
    onSuccess: (result) => {
      queryClient.setQueryData(attemptResultQueryKey(attemptId), result);
    },
  });
}

export function useLogTabSwitchMutation(attemptId: string) {
  return useMutation({
    mutationFn: () => attemptApi.logTabSwitch(attemptId),
  });
}

export function useLogProctoringEventMutation(attemptId: string) {
  return useMutation({
    mutationFn: (body: ProctoringEventRequest) => attemptApi.logProctoringEvent(attemptId, body),
  });
}

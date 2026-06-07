import { useQuery } from "@tanstack/react-query";

import { analyticsApi } from "../api/analyticsApi";
import type { StudentHistoryParams } from "../api/types";

export const studentAnalyticsQueryKey = ["analytics", "me"] as const;

export function useStudentAnalyticsQuery() {
  return useQuery({
    queryKey: studentAnalyticsQueryKey,
    queryFn: analyticsApi.getMe,
  });
}

export function studentHistoryQueryKey(params: StudentHistoryParams) {
  return ["analytics", "me", "history", params] as const;
}

export function useStudentHistoryQuery(params: StudentHistoryParams = {}) {
  return useQuery({
    queryKey: studentHistoryQueryKey(params),
    queryFn: () => analyticsApi.getMeHistory(params),
  });
}

import { useQuery } from "@tanstack/react-query";

import { adminAttemptsApi } from "../api/adminAttemptsApi";
import type { AdminAttemptFilters } from "../api/types";

export function adminAttemptsQueryKey(filters: AdminAttemptFilters) {
  return ["admin", "attempts", filters] as const;
}

export function useAdminAttemptsQuery(filters: AdminAttemptFilters = {}) {
  return useQuery({
    queryKey: adminAttemptsQueryKey(filters),
    queryFn: () => adminAttemptsApi.list(filters),
  });
}

export function adminAttemptAuditQueryKey(attemptId: string) {
  return ["admin", "attempts", attemptId, "audit"] as const;
}

export function useAttemptAuditQuery(attemptId: string) {
  return useQuery({
    queryKey: adminAttemptAuditQueryKey(attemptId),
    queryFn: () => adminAttemptsApi.getAudit(attemptId),
    enabled: Boolean(attemptId),
  });
}

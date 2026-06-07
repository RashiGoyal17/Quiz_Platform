import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type { AdminAttemptFilters, AttemptAdminItem, AttemptAuditResponse } from "./types";

export const adminAttemptsApi = {
  async list(filters: AdminAttemptFilters = {}): Promise<AttemptAdminItem[]> {
    const { data } = await apiClient.get<AttemptAdminItem[]>(ENDPOINTS.adminAttempts.list, {
      params: {
        status: filters.status,
        quiz_id: filters.quizId,
        student_id: filters.studentId,
        limit: filters.limit,
        offset: filters.offset,
      },
    });
    return data;
  },

  async getAudit(attemptId: string): Promise<AttemptAuditResponse> {
    const { data } = await apiClient.get<AttemptAuditResponse>(
      ENDPOINTS.adminAttempts.audit(attemptId),
    );
    return data;
  },
};

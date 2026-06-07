import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type { StudentAnalytics, StudentHistoryParams, StudentHistoryResponse } from "./types";

export const analyticsApi = {
  async getMe(): Promise<StudentAnalytics> {
    const { data } = await apiClient.get<StudentAnalytics>(ENDPOINTS.analytics.me);
    return data;
  },

  async getMeHistory(params: StudentHistoryParams = {}): Promise<StudentHistoryResponse> {
    const { data } = await apiClient.get<StudentHistoryResponse>(ENDPOINTS.analytics.meHistory, {
      params: {
        limit: params.limit,
        offset: params.offset,
        quiz_id: params.quizId,
      },
    });
    return data;
  },
};

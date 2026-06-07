import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type { QuestionCreateRequest, QuestionRecord, QuestionUpdateRequest } from "./types";

export const questionApi = {
  async listByBank(bankId: string): Promise<QuestionRecord[]> {
    const { data } = await apiClient.get<QuestionRecord[]>(
      ENDPOINTS.questions.listByBank(bankId),
    );
    return data;
  },

  async create(bankId: string, body: QuestionCreateRequest): Promise<QuestionRecord> {
    const { data } = await apiClient.post<QuestionRecord>(
      ENDPOINTS.questions.create(bankId),
      body,
    );
    return data;
  },

  async update(id: string, body: QuestionUpdateRequest): Promise<QuestionRecord> {
    const { data } = await apiClient.put<QuestionRecord>(ENDPOINTS.questions.update(id), body);
    return data;
  },

  async remove(id: string): Promise<void> {
    await apiClient.delete(ENDPOINTS.questions.delete(id));
  },
};

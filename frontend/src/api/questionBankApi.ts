import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type {
  QuestionBank,
  QuestionBankCreateRequest,
  QuestionBankUpdateRequest,
} from "./types";

export const questionBankApi = {
  async list(): Promise<QuestionBank[]> {
    const { data } = await apiClient.get<QuestionBank[]>(ENDPOINTS.questionBanks.list);
    return data;
  },

  async create(body: QuestionBankCreateRequest): Promise<QuestionBank> {
    const { data } = await apiClient.post<QuestionBank>(ENDPOINTS.questionBanks.create, body);
    return data;
  },

  async update(id: string, body: QuestionBankUpdateRequest): Promise<QuestionBank> {
    const { data } = await apiClient.put<QuestionBank>(ENDPOINTS.questionBanks.update(id), body);
    return data;
  },

  async remove(id: string): Promise<void> {
    await apiClient.delete(ENDPOINTS.questionBanks.delete(id));
  },
};

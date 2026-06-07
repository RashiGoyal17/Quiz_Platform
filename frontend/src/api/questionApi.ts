import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type {
  BulkImportResponse,
  QuestionCreateRequest,
  QuestionRecord,
  QuestionUpdateRequest,
} from "./types";

export type ImportFormat = "csv" | "json";

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

  async importFromFile(
    bankId: string,
    file: File,
    format: ImportFormat,
  ): Promise<BulkImportResponse> {
    const form = new FormData();
    form.append("file", file);
    form.append("format", format);
    const { data } = await apiClient.post<BulkImportResponse>(
      ENDPOINTS.questions.import(bankId),
      form,
    );
    return data;
  },
};

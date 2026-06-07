import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type {
  AnswerResponse,
  AttemptResponse,
  AttemptResultResponse,
  ProctoringEventRequest,
  ProctoringEventResponse,
  SaveAnswerRequest,
  StartAttemptRequest,
  TabSwitchResponse,
} from "./types";

export const attemptApi = {
  async start(body: StartAttemptRequest): Promise<AttemptResponse> {
    const { data } = await apiClient.post<AttemptResponse>(ENDPOINTS.attempts.start, body);
    return data;
  },

  async saveAnswer(attemptId: string, body: SaveAnswerRequest): Promise<AnswerResponse> {
    const { data } = await apiClient.post<AnswerResponse>(
      ENDPOINTS.attempts.answers(attemptId),
      body,
    );
    return data;
  },

  async submit(attemptId: string): Promise<AttemptResultResponse> {
    const { data } = await apiClient.post<AttemptResultResponse>(
      ENDPOINTS.attempts.submit(attemptId),
    );
    return data;
  },

  async getResult(attemptId: string): Promise<AttemptResultResponse> {
    const { data } = await apiClient.get<AttemptResultResponse>(
      ENDPOINTS.attempts.result(attemptId),
    );
    return data;
  },

  async logTabSwitch(attemptId: string): Promise<TabSwitchResponse> {
    const { data } = await apiClient.post<TabSwitchResponse>(
      ENDPOINTS.attempts.tabSwitch(attemptId),
    );
    return data;
  },

  async logProctoringEvent(
    attemptId: string,
    body: ProctoringEventRequest,
  ): Promise<ProctoringEventResponse> {
    const { data } = await apiClient.post<ProctoringEventResponse>(
      ENDPOINTS.attempts.proctoringEvent(attemptId),
      body,
    );
    return data;
  },
};

import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type {
  AddQuestionToQuizRequest,
  Quiz,
  QuizAvailable,
  QuizCreateRequest,
  QuizQuestion,
  QuizUpdateRequest,
} from "./types";

export const quizApi = {
  async list(): Promise<Quiz[]> {
    const { data } = await apiClient.get<Quiz[]>(ENDPOINTS.quizzes.list);
    return data;
  },

  async available(): Promise<QuizAvailable[]> {
    const { data } = await apiClient.get<QuizAvailable[]>(ENDPOINTS.quizzes.available);
    return data;
  },

  async getById(id: string): Promise<Quiz> {
    const { data } = await apiClient.get<Quiz>(ENDPOINTS.quizzes.detail(id));
    return data;
  },

  async create(body: QuizCreateRequest): Promise<Quiz> {
    const { data } = await apiClient.post<Quiz>(ENDPOINTS.quizzes.create, body);
    return data;
  },

  async update(id: string, body: QuizUpdateRequest): Promise<Quiz> {
    const { data } = await apiClient.put<Quiz>(ENDPOINTS.quizzes.update(id), body);
    return data;
  },

  async publish(id: string): Promise<Quiz> {
    const { data } = await apiClient.post<Quiz>(ENDPOINTS.quizzes.publish(id));
    return data;
  },

  async unpublish(id: string): Promise<Quiz> {
    const { data } = await apiClient.post<Quiz>(ENDPOINTS.quizzes.unpublish(id));
    return data;
  },

  async listQuizQuestions(quizId: string): Promise<QuizQuestion[]> {
    const { data } = await apiClient.get<QuizQuestion[]>(ENDPOINTS.quizzes.questions(quizId));
    return data;
  },

  async addQuestionToQuiz(quizId: string, body: AddQuestionToQuizRequest): Promise<QuizQuestion> {
    const { data } = await apiClient.post<QuizQuestion>(
      ENDPOINTS.quizzes.questions(quizId),
      body,
    );
    return data;
  },

  async removeQuestionFromQuiz(quizId: string, questionId: string): Promise<void> {
    await apiClient.delete(ENDPOINTS.quizzes.removeQuestion(quizId, questionId));
  },
};

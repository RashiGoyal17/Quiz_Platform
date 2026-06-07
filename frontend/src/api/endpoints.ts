export const ENDPOINTS = {
  auth: {
    register: "/auth/register",
    login: "/auth/login",
    refresh: "/auth/refresh",
    logout: "/auth/logout",
    me: "/auth/me",
  },
  questionBanks: {
    list: "/question-banks",
    create: "/question-banks",
    detail: (id: string) => `/question-banks/${id}`,
    update: (id: string) => `/question-banks/${id}`,
    delete: (id: string) => `/question-banks/${id}`,
  },
  questions: {
    listByBank: (bankId: string) => `/question-banks/${bankId}/questions`,
    create: (bankId: string) => `/question-banks/${bankId}/questions`,
    detail: (id: string) => `/questions/${id}`,
    update: (id: string) => `/questions/${id}`,
    delete: (id: string) => `/questions/${id}`,
  },
  quizzes: {
    list: "/quizzes",
    create: "/quizzes",
    available: "/quizzes/available",
    detail: (id: string) => `/quizzes/${id}`,
    update: (id: string) => `/quizzes/${id}`,
    publish: (id: string) => `/quizzes/${id}/publish`,
    unpublish: (id: string) => `/quizzes/${id}/unpublish`,
    questions: (id: string) => `/quizzes/${id}/questions`,
    removeQuestion: (id: string, questionId: string) =>
      `/quizzes/${id}/questions/${questionId}`,
  },
  attempts: {
    start: "/attempts/start",
    answers: (attemptId: string) => `/attempts/${attemptId}/answers`,
    submit: (attemptId: string) => `/attempts/${attemptId}/submit`,
    result: (attemptId: string) => `/attempts/${attemptId}/result`,
    tabSwitch: (attemptId: string) => `/attempts/${attemptId}/tab-switch`,
    proctoringEvent: (attemptId: string) => `/attempts/${attemptId}/proctoring-event`,
  },
  analytics: {
    me: "/analytics/me",
    meHistory: "/analytics/me/history",
    adminDashboard: "/analytics/admin/dashboard",
  },
  adminAttempts: {
    list: "/admin/attempts",
    audit: (attemptId: string) => `/admin/attempts/${attemptId}/audit`,
  },
} as const;

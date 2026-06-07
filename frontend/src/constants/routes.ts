export const ROUTES = {
  root: "/",
  login: "/login",
  register: "/register",
  admin: {
    dashboard: "/admin/dashboard",
    questionBanks: "/admin/question-banks",
    questions: "/admin/questions",
    quizzes: "/admin/quizzes",
    quizBuilderPath: "/admin/quizzes/:quizId",
    quizBuilder: (quizId: string) => `/admin/quizzes/${quizId}`,
    attempts: "/admin/attempts",
    attemptDetailPath: "/admin/attempts/:attemptId",
    attemptDetail: (attemptId: string) => `/admin/attempts/${attemptId}`,
  },
  student: {
    dashboard: "/student/dashboard",
    quizzes: "/student/quizzes",
    attemptDetailPath: "/student/attempts/:attemptId",
    attemptDetail: (attemptId: string, quizId?: string) =>
      quizId
        ? `/student/attempts/${attemptId}?quizId=${quizId}`
        : `/student/attempts/${attemptId}`,
    attemptResultPath: "/student/attempts/:attemptId/result",
    attemptResult: (attemptId: string) => `/student/attempts/${attemptId}/result`,
    results: "/student/results",
    analytics: "/student/analytics",
  },
} as const;

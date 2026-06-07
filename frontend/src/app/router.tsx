import { createBrowserRouter } from "react-router-dom";

import { AdminLayout } from "../components/layout/AdminLayout";
import { StudentLayout } from "../components/layout/StudentLayout";
import { ProtectedRoute } from "../components/routing/ProtectedRoute";
import { RoleGuard } from "../components/routing/RoleGuard";
import { RoleRedirect } from "../components/routing/RoleRedirect";
import { ROUTES } from "../constants/routes";
import { NotFoundPage } from "../pages/NotFoundPage";
import { AdminAttemptDetailPage } from "../pages/admin/AdminAttemptDetailPage";
import { AdminAttemptsPage } from "../pages/admin/AdminAttemptsPage";
import { AdminDashboardPage } from "../pages/admin/AdminDashboardPage";
import { QuestionBanksPage } from "../pages/admin/QuestionBanksPage";
import { QuestionsPage } from "../pages/admin/QuestionsPage";
import { QuizBuilderPage } from "../pages/admin/QuizBuilderPage";
import { QuizzesPage } from "../pages/admin/QuizzesPage";
import { LoginPage } from "../pages/auth/LoginPage";
import { RegisterPage } from "../pages/auth/RegisterPage";
import { AnalyticsPage } from "../pages/student/AnalyticsPage";
import { AttemptDetailPage } from "../pages/student/AttemptDetailPage";
import { AttemptResultPage } from "../pages/student/AttemptResultPage";
import { AvailableQuizzesPage } from "../pages/student/AvailableQuizzesPage";
import { ResultsPage } from "../pages/student/ResultsPage";
import { StudentDashboardPage } from "../pages/student/StudentDashboardPage";

export const router = createBrowserRouter([
  { path: ROUTES.root, element: <RoleRedirect /> },
  { path: ROUTES.login, element: <LoginPage /> },
  { path: ROUTES.register, element: <RegisterPage /> },

  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <RoleGuard role="admin" />,
        children: [
          {
            element: <AdminLayout />,
            children: [
              { path: ROUTES.admin.dashboard, element: <AdminDashboardPage /> },
              { path: ROUTES.admin.questionBanks, element: <QuestionBanksPage /> },
              { path: ROUTES.admin.questions, element: <QuestionsPage /> },
              { path: ROUTES.admin.quizzes, element: <QuizzesPage /> },
              { path: ROUTES.admin.quizBuilderPath, element: <QuizBuilderPage /> },
              { path: ROUTES.admin.attempts, element: <AdminAttemptsPage /> },
              { path: ROUTES.admin.attemptDetailPath, element: <AdminAttemptDetailPage /> },
            ],
          },
        ],
      },
      {
        element: <RoleGuard role="student" />,
        children: [
          {
            element: <StudentLayout />,
            children: [
              { path: ROUTES.student.dashboard, element: <StudentDashboardPage /> },
              { path: ROUTES.student.quizzes, element: <AvailableQuizzesPage /> },
              { path: ROUTES.student.attemptDetailPath, element: <AttemptDetailPage /> },
              { path: ROUTES.student.attemptResultPath, element: <AttemptResultPage /> },
              { path: ROUTES.student.results, element: <ResultsPage /> },
              { path: ROUTES.student.analytics, element: <AnalyticsPage /> },
            ],
          },
        ],
      },
    ],
  },

  { path: "*", element: <NotFoundPage /> },
]);

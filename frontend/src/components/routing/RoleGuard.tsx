import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import type { UserRole } from "../../api/types";
import { ROUTES } from "../../constants/routes";

const HOME_BY_ROLE: Record<UserRole, string> = {
  admin: ROUTES.admin.dashboard,
  student: ROUTES.student.dashboard,
};

/**
 * Restricts a route subtree to a single role. Mirrors the backend's
 * require_admin / require_student split — a logged-in user with the
 * wrong role is redirected to their own dashboard rather than /login.
 */
export function RoleGuard({ role }: { role: UserRole }) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== role) {
    return <Navigate to={HOME_BY_ROLE[user.role]} replace />;
  }

  return <Outlet />;
}

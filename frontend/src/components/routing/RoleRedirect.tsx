import { Navigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { ROUTES } from "../../constants/routes";
import { LoadingState } from "../common/LoadingState";

/** Sends an authenticated user to their role's dashboard; otherwise to /login. */
export function RoleRedirect() {
  const { status, user } = useAuth();

  if (status === "loading") {
    return <LoadingState message="Loading your account..." />;
  }

  if (status === "unauthenticated" || !user) {
    return <Navigate to={ROUTES.login} replace />;
  }

  return (
    <Navigate
      to={user.role === "admin" ? ROUTES.admin.dashboard : ROUTES.student.dashboard}
      replace
    />
  );
}

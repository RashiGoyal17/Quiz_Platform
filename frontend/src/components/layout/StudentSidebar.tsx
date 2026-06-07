import AssessmentIcon from "@mui/icons-material/Assessment";
import AssignmentTurnedInIcon from "@mui/icons-material/AssignmentTurnedIn";
import DashboardIcon from "@mui/icons-material/Dashboard";
import QuizIcon from "@mui/icons-material/Quiz";

import { ROUTES } from "../../constants/routes";
import { ResponsiveSidebar, type SidebarNavItem } from "./ResponsiveSidebar";

const NAV_ITEMS: SidebarNavItem[] = [
  { label: "Dashboard", to: ROUTES.student.dashboard, icon: <DashboardIcon /> },
  { label: "Available Quizzes", to: ROUTES.student.quizzes, icon: <QuizIcon /> },
  { label: "Results", to: ROUTES.student.results, icon: <AssignmentTurnedInIcon /> },
  { label: "Analytics", to: ROUTES.student.analytics, icon: <AssessmentIcon /> },
];

interface StudentSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

export function StudentSidebar(props: StudentSidebarProps) {
  return <ResponsiveSidebar navItems={NAV_ITEMS} {...props} />;
}

import AssignmentIcon from "@mui/icons-material/Assignment";
import DashboardIcon from "@mui/icons-material/Dashboard";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import HelpCenterIcon from "@mui/icons-material/HelpCenter";
import QuizIcon from "@mui/icons-material/Quiz";

import { ROUTES } from "../../constants/routes";
import { ResponsiveSidebar, type SidebarNavItem } from "./ResponsiveSidebar";

const NAV_ITEMS: SidebarNavItem[] = [
  { label: "Dashboard", to: ROUTES.admin.dashboard, icon: <DashboardIcon /> },
  { label: "Question Banks", to: ROUTES.admin.questionBanks, icon: <QuizIcon /> },
  { label: "Questions", to: ROUTES.admin.questions, icon: <HelpCenterIcon /> },
  { label: "Quizzes", to: ROUTES.admin.quizzes, icon: <AssignmentIcon /> },
  { label: "Attempts", to: ROUTES.admin.attempts, icon: <FactCheckIcon /> },
];

interface AdminSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

export function AdminSidebar(props: AdminSidebarProps) {
  return <ResponsiveSidebar navItems={NAV_ITEMS} {...props} />;
}

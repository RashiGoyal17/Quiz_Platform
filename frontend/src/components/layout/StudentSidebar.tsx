import AssessmentIcon from "@mui/icons-material/Assessment";
import AssignmentTurnedInIcon from "@mui/icons-material/AssignmentTurnedIn";
import DashboardIcon from "@mui/icons-material/Dashboard";
import QuizIcon from "@mui/icons-material/Quiz";
import { Drawer, List, ListItemButton, ListItemIcon, ListItemText } from "@mui/material";
import { Link as RouterLink, useLocation } from "react-router-dom";

import { ROUTES } from "../../constants/routes";

const SIDEBAR_WIDTH = 240;

const NAV_ITEMS = [
  { label: "Dashboard", to: ROUTES.student.dashboard, icon: <DashboardIcon /> },
  { label: "Available Quizzes", to: ROUTES.student.quizzes, icon: <QuizIcon /> },
  { label: "Results", to: ROUTES.student.results, icon: <AssignmentTurnedInIcon /> },
  { label: "Analytics", to: ROUTES.student.analytics, icon: <AssessmentIcon /> },
];

export function StudentSidebar() {
  const { pathname } = useLocation();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: SIDEBAR_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: SIDEBAR_WIDTH, boxSizing: "border-box" },
      }}
    >
      <List sx={{ pt: 1 }}>
        {NAV_ITEMS.map((item) => (
          <ListItemButton
            key={item.to}
            component={RouterLink}
            to={item.to}
            selected={pathname === item.to || pathname.startsWith(`${item.to}/`)}
            sx={{
              "&.Mui-selected": {
                bgcolor: "action.selected",
                "& .MuiListItemIcon-root, & .MuiListItemText-primary": {
                  color: "primary.main",
                  fontWeight: 600,
                },
              },
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  );
}

export { SIDEBAR_WIDTH };

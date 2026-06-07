import { Box, Container } from "@mui/material";
import { Outlet } from "react-router-dom";

import { useSidebarState } from "../../hooks/useSidebarState";
import { Navbar } from "./Navbar";
import { StudentSidebar } from "./StudentSidebar";

export function StudentLayout() {
  const sidebar = useSidebarState("student_sidebar_collapsed");

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <Navbar title="Quiz Platform — Student" onMenuClick={sidebar.openMobile} />
      <Box sx={{ display: "flex", flex: 1 }}>
        <StudentSidebar
          mobileOpen={sidebar.mobileOpen}
          onMobileClose={sidebar.closeMobile}
          collapsed={sidebar.collapsed}
          onToggleCollapsed={sidebar.toggleCollapsed}
        />
        <Container maxWidth="lg" sx={{ py: 4, flex: 1 }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
}

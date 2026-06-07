import { Box, Container } from "@mui/material";
import { Outlet } from "react-router-dom";

import { useSidebarState } from "../../hooks/useSidebarState";
import { AdminSidebar } from "./AdminSidebar";
import { Navbar } from "./Navbar";

export function AdminLayout() {
  const sidebar = useSidebarState("admin_sidebar_collapsed");

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <Navbar title="Quiz Platform — Admin" onMenuClick={sidebar.openMobile} />
      <Box sx={{ display: "flex", flex: 1, gap: 2 }}>
        <AdminSidebar
          mobileOpen={sidebar.mobileOpen}
          onMobileClose={sidebar.closeMobile}
          collapsed={sidebar.collapsed}
          onToggleCollapsed={sidebar.toggleCollapsed}
        />
        <Container maxWidth="lg" sx={{ py: 4, flex: 1, bgcolor: "background.paper" }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
}

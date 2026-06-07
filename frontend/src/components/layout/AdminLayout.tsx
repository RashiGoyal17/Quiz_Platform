import { Box, Container } from "@mui/material";
import { Outlet } from "react-router-dom";

import { AdminSidebar } from "./AdminSidebar";
import { Navbar } from "./Navbar";

export function AdminLayout() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <Navbar title="Quiz Platform — Admin" />
      <Box sx={{ display: "flex", flex: 1 }}>
        <AdminSidebar />
        <Container maxWidth="lg" sx={{ py: 4, flex: 1 }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
}

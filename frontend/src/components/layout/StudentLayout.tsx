import { Box, Container } from "@mui/material";
import { Outlet } from "react-router-dom";

import { Navbar } from "./Navbar";
import { StudentSidebar } from "./StudentSidebar";

export function StudentLayout() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <Navbar title="Quiz Platform — Student" />
      <Box sx={{ display: "flex", flex: 1 }}>
        <StudentSidebar />
        <Container maxWidth="lg" sx={{ py: 4, flex: 1 }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
}

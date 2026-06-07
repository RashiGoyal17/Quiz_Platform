import { Box, Paper, Typography } from "@mui/material";

import { useAuth } from "../../context/AuthContext";

export function AdminDashboardPage() {
  const { user } = useAuth();

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Typography variant="h4">Admin Dashboard</Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Welcome back, {user?.name}. Platform metrics, question bank management,
          quiz management, analytics, and audit tools will appear here in upcoming phases.
        </Typography>
      </Paper>
    </Box>
  );
}

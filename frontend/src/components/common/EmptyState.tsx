import { Box, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title?: string;
  message?: string;
  action?: ReactNode;
}

export function EmptyState({
  title = "Nothing here yet",
  message,
  action,
}: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 1,
        py: 6,
        textAlign: "center",
      }}
    >
      <Typography variant="h6">{title}</Typography>
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
      {action}
    </Box>
  );
}

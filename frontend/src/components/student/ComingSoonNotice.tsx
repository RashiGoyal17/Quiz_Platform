import { Box, Paper, Typography } from "@mui/material";

interface ComingSoonNoticeProps {
  title: string;
  message: string;
}

export function ComingSoonNotice({ title, message }: ComingSoonNoticeProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <Typography variant="h4">{title}</Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">{message}</Typography>
      </Paper>
    </Box>
  );
}

import { Box, Paper, Stack, Typography } from "@mui/material";

interface QuestionNavigatorProps {
  total: number;
  currentIndex: number;
  answeredFlags: boolean[];
  onJump: (index: number) => void;
  disabled?: boolean;
}

export function QuestionNavigator({
  total,
  currentIndex,
  answeredFlags,
  onJump,
  disabled = false,
}: QuestionNavigatorProps) {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
        Questions
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
        {Array.from({ length: total }, (_, index) => {
          const isCurrent = index === currentIndex;
          const isAnswered = answeredFlags[index];

          return (
            <Box
              key={index}
              component="button"
              type="button"
              onClick={() => onJump(index)}
              disabled={disabled}
              sx={{
                width: 40,
                height: 40,
                borderRadius: 1,
                border: "1px solid",
                borderColor: isCurrent ? "primary.main" : isAnswered ? "success.main" : "divider",
                bgcolor: isCurrent
                  ? "primary.main"
                  : isAnswered
                    ? "success.light"
                    : "transparent",
                color: isCurrent ? "primary.contrastText" : "text.primary",
                fontWeight: isCurrent ? 700 : 500,
                cursor: disabled ? "not-allowed" : "pointer",
                opacity: disabled ? 0.6 : 1,
                fontSize: "0.875rem",
                fontFamily: "inherit",
              }}
            >
              {index + 1}
            </Box>
          );
        })}
      </Box>

      <Stack direction="row" spacing={2} sx={{ mt: 2, flexWrap: "wrap" }}>
        <LegendItem color="primary.main" label="Current" filled />
        <LegendItem color="success.light" borderColor="success.main" label="Answered" filled />
        <LegendItem color="transparent" borderColor="divider" label="Unanswered" />
      </Stack>
    </Paper>
  );
}

interface LegendItemProps {
  color: string;
  borderColor?: string;
  label: string;
  filled?: boolean;
}

function LegendItem({ color, borderColor, label, filled = false }: LegendItemProps) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
      <Box
        sx={{
          width: 16,
          height: 16,
          borderRadius: 0.5,
          border: "1px solid",
          borderColor: borderColor ?? color,
          bgcolor: filled ? color : "transparent",
        }}
      />
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
}

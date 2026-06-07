import AccessTimeIcon from "@mui/icons-material/AccessTime";
import { Box, Chip } from "@mui/material";
import { useEffect, useRef, useState } from "react";

interface QuizTimerProps {
  deadline: number;
  onExpire: () => void;
}

function formatRemaining(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");
  return hours > 0 ? `${hours}:${pad(minutes)}:${pad(seconds)}` : `${pad(minutes)}:${pad(seconds)}`;
}

export function QuizTimer({ deadline, onExpire }: QuizTimerProps) {
  const [remaining, setRemaining] = useState(() => deadline - Date.now());
  const hasExpiredRef = useRef(false);

  useEffect(() => {
    hasExpiredRef.current = false;
    const tick = () => {
      const next = deadline - Date.now();
      setRemaining(next);
      if (next <= 0 && !hasExpiredRef.current) {
        hasExpiredRef.current = true;
        onExpire();
      }
    };

    tick();
    const intervalId = window.setInterval(tick, 1000);
    return () => window.clearInterval(intervalId);
  }, [deadline, onExpire]);

  const isLow = remaining <= 60_000 && remaining > 0;

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Chip
        icon={<AccessTimeIcon />}
        label={`Time remaining: ${formatRemaining(remaining)}`}
        color={remaining <= 0 ? "error" : isLow ? "warning" : "default"}
        variant={remaining <= 0 || isLow ? "filled" : "outlined"}
      />
    </Box>
  );
}

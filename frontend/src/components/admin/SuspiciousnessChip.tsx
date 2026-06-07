import { Chip } from "@mui/material";

import { SUSPICIOUSNESS_COLORS, type SuspiciousnessLevel } from "../../utils/suspiciousness";

interface SuspiciousnessChipProps {
  level: SuspiciousnessLevel;
}

export function SuspiciousnessChip({ level }: SuspiciousnessChipProps) {
  return (
    <Chip size="small" label={level} color={SUSPICIOUSNESS_COLORS[level]} variant="outlined" />
  );
}

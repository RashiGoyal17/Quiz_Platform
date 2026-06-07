import { Card, CardContent, Typography } from "@mui/material";

interface StatCardProps {
  label: string;
  value: string;
}

export function StatCard({ label, value }: StatCardProps) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h4">{value}</Typography>
      </CardContent>
    </Card>
  );
}

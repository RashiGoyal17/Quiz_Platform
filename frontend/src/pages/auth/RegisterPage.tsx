import { useState, type FormEvent } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Link,
  MenuItem,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { isAxiosError } from "axios";

import { useAuth } from "../../context/AuthContext";
import type { ApiErrorResponse, UserRole } from "../../api/types";
import { ROUTES } from "../../constants/routes";

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "student", label: "Student" },
  { value: "admin", label: "Admin" },
];

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("student");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await register({ name, email, password, role });
      navigate(user.role === "admin" ? ROUTES.admin.dashboard : ROUTES.student.dashboard, {
        replace: true,
      });
    } catch (err) {
      const detail = isAxiosError<ApiErrorResponse>(err)
        ? err.response?.data?.detail
        : undefined;
      setError(detail ?? "Registration failed. Please check your details and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
        px: 2,
      }}
    >
      <Paper elevation={2} sx={{ p: 4, width: "100%", maxWidth: 420 }}>
        <Typography variant="h5" gutterBottom>
          Create an account
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Online Quiz Platform
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{ display: "flex", flexDirection: "column", gap: 2 }}
        >
          <TextField
            label="Full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            fullWidth
          />
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            fullWidth
          />
          <TextField
            label="Password"
            type="password"
            helperText="At least 8 characters, with uppercase, lowercase, digit, and special character."
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            fullWidth
          />
          <TextField
            select
            label="Role"
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            fullWidth
          >
            {ROLE_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>
          <Button type="submit" variant="contained" size="large" disabled={submitting}>
            {submitting ? "Creating account..." : "Register"}
          </Button>
        </Box>

        <Typography variant="body2" sx={{ mt: 3 }}>
          Already have an account?{" "}
          <Link component={RouterLink} to={ROUTES.login}>
            Sign in
          </Link>
        </Typography>
      </Paper>
    </Box>
  );
}

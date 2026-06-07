import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import { AppBar, Box, Chip, IconButton, Toolbar, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

interface NavbarProps {
  title: string;
  onMenuClick?: () => void;
}

export function Navbar({ title, onMenuClick }: NavbarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <AppBar position="static" color="primary" elevation={1}>
      <Toolbar sx={{ gap: 2 }}>
        {onMenuClick && (
          <IconButton
            color="inherit"
            edge="start"
            onClick={onMenuClick}
            aria-label="Open navigation menu"
            sx={{ display: { xs: "inline-flex", md: "none" } }}
          >
            <MenuIcon />
          </IconButton>
        )}
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          {title}
        </Typography>
        {user && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Typography variant="body2">{user.name}</Typography>
            <Chip
              label={user.role}
              size="small"
              color="secondary"
              sx={{ textTransform: "capitalize" }}
            />
            <IconButton color="inherit" onClick={handleLogout} aria-label="Log out">
              <LogoutIcon />
            </IconButton>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}

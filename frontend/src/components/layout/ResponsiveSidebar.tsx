import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import {
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
} from "@mui/material";
import type { ReactNode } from "react";
import { Link as RouterLink, useLocation } from "react-router-dom";

export const SIDEBAR_WIDTH = 240;
export const SIDEBAR_COLLAPSED_WIDTH = 72;

export interface SidebarNavItem {
  label: string;
  to: string;
  icon: ReactNode;
}

interface ResponsiveSidebarProps {
  navItems: SidebarNavItem[];
  mobileOpen: boolean;
  onMobileClose: () => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

/**
 * Shared responsive drawer shell used by AdminSidebar and StudentSidebar.
 * Below `md`: a temporary (overlay) drawer toggled via the navbar's menu button.
 * At `md` and above: a permanent drawer that can collapse to an icon rail.
 */
export function ResponsiveSidebar({
  navItems,
  mobileOpen,
  onMobileClose,
  collapsed,
  onToggleCollapsed,
}: ResponsiveSidebarProps) {
  const { pathname } = useLocation();
  const width = collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;

  const renderNavList = (onItemClick?: () => void) => (
    <List sx={{ pt: 1 }}>
      {navItems.map((item) => {
        const selected = pathname === item.to || pathname.startsWith(`${item.to}/`);
        return (
          <Tooltip
            key={item.to}
            title={collapsed ? item.label : ""}
            placement="right"
            arrow
            disableHoverListener={!collapsed}
            disableFocusListener={!collapsed}
            disableTouchListener={!collapsed}
          >
            <ListItemButton
              component={RouterLink}
              to={item.to}
              selected={selected}
              onClick={onItemClick}
              sx={{
                justifyContent: collapsed ? "center" : "flex-start",
                px: collapsed ? 1.5 : 2,
                "&.Mui-selected": {
                  bgcolor: "action.selected",
                  "& .MuiListItemIcon-root, & .MuiListItemText-primary": {
                    color: "primary.main",
                    fontWeight: 600,
                  },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 0, mr: collapsed ? 0 : 2, justifyContent: "center" }}>
                {item.icon}
              </ListItemIcon>
              {!collapsed && <ListItemText primary={item.label} />}
            </ListItemButton>
          </Tooltip>
        );
      })}
    </List>
  );

  return (
    <Box component="nav" sx={{ width: { md: width }, flexShrink: { md: 0 } }}>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", md: "none" },
          [`& .MuiDrawer-paper`]: { width: SIDEBAR_WIDTH, boxSizing: "border-box" },
        }}
      >
        {renderNavList(onMobileClose)}
      </Drawer>

      <Drawer
        variant="permanent"
        open
        sx={{
          display: { xs: "none", md: "block" },
          width,
          [`& .MuiDrawer-paper`]: {
            width,
            boxSizing: "border-box",
            overflowX: "hidden",
            transition: (theme) =>
              theme.transitions.create("width", {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
          },
        }}
      >
        <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
          {renderNavList()}
          <Divider sx={{ mt: "auto" }} />
          <Box
            sx={{
              display: "flex",
              justifyContent: collapsed ? "center" : "flex-end",
              px: 1,
              py: 0.5,
            }}
          >
            <IconButton
              onClick={onToggleCollapsed}
              size="small"
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {collapsed ? <ChevronRightIcon /> : <ChevronLeftIcon />}
            </IconButton>
          </Box>
        </Box>
      </Drawer>
    </Box>
  );
}

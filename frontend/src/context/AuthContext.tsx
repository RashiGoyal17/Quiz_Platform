import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { authApi } from "../api/authApi";
import { apiClient } from "../api/axiosClient";
import { ENDPOINTS } from "../api/endpoints";
import { tokenStore } from "../api/tokenStore";
import type { LoginRequest, RegisterRequest, TokenResponse, UserInfo } from "../api/types";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: UserInfo | null;
  status: AuthStatus;
  login: (credentials: LoginRequest) => Promise<UserInfo>;
  register: (payload: RegisterRequest) => Promise<UserInfo>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function applySession(session: TokenResponse): UserInfo {
  tokenStore.setAccessToken(session.access_token);
  tokenStore.setRefreshToken(session.refresh_token);
  return session.user;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const clearSession = useCallback(() => {
    tokenStore.clear();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  // Forced logout, triggered by the Axios interceptor when refresh rotation fails.
  useEffect(() => {
    tokenStore.setSessionExpiredHandler(clearSession);
    return () => tokenStore.setSessionExpiredHandler(null);
  }, [clearSession]);

  // Restore session on load using the persisted refresh token (rotates it,
  // since the backend revokes refresh tokens after a single use).
  useEffect(() => {
    const refreshToken = tokenStore.getRefreshToken();
    if (!refreshToken) {
      setStatus("unauthenticated");
      return;
    }

    apiClient
      .post<TokenResponse>(ENDPOINTS.auth.refresh, { refresh_token: refreshToken })
      .then(({ data }) => {
        setUser(applySession(data));
        setStatus("authenticated");
      })
      .catch(() => {
        clearSession();
      });
  }, [clearSession]);

  const login = useCallback(async (credentials: LoginRequest) => {
    const session = await authApi.login(credentials);
    const loggedInUser = applySession(session);
    setUser(loggedInUser);
    setStatus("authenticated");
    return loggedInUser;
  }, []);

  const register = useCallback(async (payload: RegisterRequest) => {
    const session = await authApi.register(payload);
    const registeredUser = applySession(session);
    setUser(registeredUser);
    setStatus("authenticated");
    return registeredUser;
  }, []);

  const logout = useCallback(async () => {
    const refreshToken = tokenStore.getRefreshToken();
    if (refreshToken) {
      try {
        await authApi.logout({ refresh_token: refreshToken });
      } catch {
        // Best-effort revoke — proceed with local logout regardless.
      }
    }
    clearSession();
  }, [clearSession]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}

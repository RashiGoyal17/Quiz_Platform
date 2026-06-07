/**
 * Bridges the in-memory access token (owned by AuthContext) and the
 * localStorage-persisted refresh token to the Axios layer, which sits
 * outside the React tree and cannot consume context directly.
 */

const REFRESH_TOKEN_KEY = "quiz_platform_refresh_token";

let accessToken: string | null = null;
let onSessionExpired: (() => void) | null = null;

export const tokenStore = {
  getAccessToken(): string | null {
    return accessToken;
  },

  setAccessToken(token: string | null): void {
    accessToken = token;
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setRefreshToken(token: string | null): void {
    if (token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  },

  clear(): void {
    accessToken = null;
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  /** Registered by AuthContext so the Axios interceptor can force a logout on refresh failure. */
  setSessionExpiredHandler(handler: (() => void) | null): void {
    onSessionExpired = handler;
  },

  notifySessionExpired(): void {
    onSessionExpired?.();
  },
};

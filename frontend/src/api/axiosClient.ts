import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { ENDPOINTS } from "./endpoints";
import { tokenStore } from "./tokenStore";
import type { TokenResponse } from "./types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({ baseURL });

// Plain instance for refresh calls — must NOT carry the response interceptor,
// otherwise a failed refresh would recursively trigger another refresh attempt.
const refreshClient = axios.create({ baseURL });

apiClient.interceptors.request.use((config) => {
  const token = tokenStore.getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

let refreshPromise: Promise<string | null> | null = null;

/**
 * Rotates the refresh token exactly once per concurrent burst of 401s.
 * The backend revokes the old refresh token on every /auth/refresh call,
 * so concurrent requests must share a single in-flight rotation.
 */
async function rotateRefreshToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refreshToken = tokenStore.getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  refreshPromise = refreshClient
    .post<TokenResponse>(ENDPOINTS.auth.refresh, { refresh_token: refreshToken })
    .then(({ data }) => {
      tokenStore.setAccessToken(data.access_token);
      tokenStore.setRefreshToken(data.refresh_token);
      return data.access_token;
    })
    .catch(() => null)
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined;
    const status = error.response?.status;

    const isAuthEndpoint = config?.url?.startsWith(ENDPOINTS.auth.refresh);

    if (status === 401 && config && !config._retried && !isAuthEndpoint) {
      config._retried = true;

      const newAccessToken = await rotateRefreshToken();
      if (newAccessToken) {
        config.headers.set("Authorization", `Bearer ${newAccessToken}`);
        return apiClient(config);
      }

      tokenStore.clear();
      tokenStore.notifySessionExpired();
    }

    return Promise.reject(error);
  },
);

import { apiClient } from "./axiosClient";
import { ENDPOINTS } from "./endpoints";
import type {
  LoginRequest,
  LogoutRequest,
  RegisterRequest,
  TokenResponse,
  UserInfo,
} from "./types";

export const authApi = {
  async login(body: LoginRequest): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>(ENDPOINTS.auth.login, body);
    return data;
  },

  async register(body: RegisterRequest): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>(ENDPOINTS.auth.register, body);
    return data;
  },

  async logout(body: LogoutRequest): Promise<void> {
    await apiClient.post(ENDPOINTS.auth.logout, body);
  },

  async me(): Promise<UserInfo> {
    const { data } = await apiClient.get<UserInfo>(ENDPOINTS.auth.me);
    return data;
  },
};

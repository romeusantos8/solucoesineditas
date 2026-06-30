// Cliente HTTP central. Tudo o que fala com a API Django passa por aqui.
//
// Autenticação JWT:
// - request: anexa  Authorization: Bearer <access>  se houver access guardado.
// - response: se um pedido falhar com 401 (access expirado), tenta UMA vez
//   renovar o access com o refresh token e repete o pedido original. Se o
//   refresh também falhar, limpa a sessão e manda para /login.

import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import {
  clearTokens,
  getAccess,
  getRefresh,
  setAccess,
} from "../auth/tokens";

const baseURL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api";

export const api = axios.create({ baseURL });

// Instância separada SÓ para o refresh — não tem os interceptors, para um 401
// no refresh não disparar outra tentativa de refresh (evita loop infinito).
const refreshClient = axios.create({ baseURL });

// --- Request: anexa o access token ---
api.interceptors.request.use((config) => {
  const access = getAccess();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

// Marca um pedido como "já tentei renovar", para não entrar em ciclo.
interface RetriableConfig extends InternalAxiosRequestConfig {
  _jaTentouRefresh?: boolean;
}

// --- Response: em 401, tenta renovar o access uma vez e repete o pedido ---
api.interceptors.response.use(
  (resp) => resp,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const refresh = getRefresh();

    const podeRenovar =
      error.response?.status === 401 &&
      original &&
      !original._jaTentouRefresh &&
      Boolean(refresh);

    if (!podeRenovar) {
      return Promise.reject(error);
    }

    original._jaTentouRefresh = true;
    try {
      const { data } = await refreshClient.post<{ access: string }>(
        "/auth/token/refresh/",
        { refresh },
      );
      setAccess(data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original); // repete o pedido original com o access novo
    } catch (refreshError) {
      // Refresh inválido/expirado: sessão acabou. Limpa e força novo login.
      clearTokens();
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
      return Promise.reject(refreshError);
    }
  },
);

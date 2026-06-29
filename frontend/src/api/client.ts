// Cliente HTTP central. Tudo o que fala com a API Django passa por aqui.
//
// - baseURL vem de uma variável de ambiente do Vite (VITE_API_URL), com um
//   default para desenvolvimento local.
// - um interceptor injeta automaticamente o token de autenticação (guardado no
//   localStorage) no cabeçalho Authorization de cada pedido.

import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api";

export const api = axios.create({ baseURL });

// Chave usada para guardar o token no localStorage do browser.
export const TOKEN_KEY = "gr_token";

// Antes de cada pedido sair, se houver token guardado, anexa-o.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

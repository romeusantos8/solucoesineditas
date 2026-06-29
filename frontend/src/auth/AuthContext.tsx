// Estado de autenticação partilhado por toda a app.
//
// Guardamos o token no localStorage para a sessão sobreviver a refreshes da
// página. login() troca username+password pelo token (via /api/auth/token/);
// logout() limpa-o.

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { api, TOKEN_KEY } from "../api/client";

interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(TOKEN_KEY),
  );

  async function login(username: string, password: string) {
    // O endpoint devolve { token: "..." } em caso de sucesso.
    const { data } = await api.post<{ token: string }>("/auth/token/", {
      username,
      password,
    });
    localStorage.setItem(TOKEN_KEY, data.token);
    setToken(data.token);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }

  const value = useMemo<AuthState>(
    () => ({ token, isAuthenticated: Boolean(token), login, logout }),
    [token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook de conveniência para consumir o contexto sem repetir o useContext.
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth tem de ser usado dentro de <AuthProvider>.");
  }
  return ctx;
}

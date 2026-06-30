// Estado de autenticação partilhado por toda a app.
//
// Com JWT, o login devolve um par { access, refresh } que guardamos no
// localStorage (ver auth/tokens.ts). A sessão considera-se ativa enquanto
// houver um access guardado; a renovação automática vive no interceptor do
// cliente axios (api/client.ts).

import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import { clearTokens, getAccess, setTokens } from "./tokens";

interface AuthState {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Estado booleano simples: há access guardado = sessão ativa.
  const [autenticado, setAutenticado] = useState<boolean>(() =>
    Boolean(getAccess()),
  );

  async function login(username: string, password: string) {
    // O endpoint JWT devolve { access, refresh } em caso de sucesso.
    const { data } = await api.post<{ access: string; refresh: string }>(
      "/auth/token/",
      { username, password },
    );
    setTokens(data.access, data.refresh);
    setAutenticado(true);
  }

  function logout() {
    clearTokens();
    setAutenticado(false);
  }

  const value = useMemo<AuthState>(
    () => ({ isAuthenticated: autenticado, login, logout }),
    [autenticado],
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

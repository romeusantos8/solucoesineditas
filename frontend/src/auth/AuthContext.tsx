// Provider do estado de autenticação, partilhado por toda a app.
//
// Com JWT, o login devolve um par { access, refresh } que guardamos no
// localStorage (ver auth/tokens.ts). A sessão considera-se ativa enquanto
// houver um access guardado; a renovação automática vive no interceptor do
// cliente axios (api/client.ts).
//
// Depois do login (ou ao reabrir a app com sessão) pede-se GET /eu/, que diz o
// perfil: "gestao" vê a app principal, "funcionario" só o portal de despesas.
// Uma conta "sem_acesso" (funcionário desativado) é tratada como sem sessão.
//
// O contexto e o hook estão em ficheiros próprios (authContext.ts / useAuth.ts)
// para este ficheiro exportar só o componente — requisito do fast-refresh.

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { Eu } from "../api/types";
import { clearTokens, getAccess, setTokens } from "./tokens";
import { AuthContext, type AuthState } from "./authStore";

export function AuthProvider({ children }: { children: ReactNode }) {
  // Estado booleano simples: há access guardado = sessão ativa.
  const [autenticado, setAutenticado] = useState<boolean>(() =>
    Boolean(getAccess()),
  );
  const [eu, setEu] = useState<Eu | null>(null);

  function logout() {
    clearTokens();
    setAutenticado(false);
    setEu(null);
  }

  // Sessão já existente (ex.: refresh da página): descobre o perfil.
  useEffect(() => {
    if (!autenticado || eu) return;
    api
      .get<Eu>("/eu/")
      .then(({ data }) => (data.perfil === "sem_acesso" ? logout() : setEu(data)))
      .catch(() => logout());
  }, [autenticado, eu]);

  async function login(username: string, password: string) {
    // O endpoint JWT devolve { access, refresh } em caso de sucesso.
    const { data } = await api.post<{ access: string; refresh: string }>(
      "/auth/token/",
      { username, password },
    );
    setTokens(data.access, data.refresh);
    const { data: perfil } = await api.get<Eu>("/eu/");
    if (perfil.perfil === "sem_acesso") {
      clearTokens();
    } else {
      setEu(perfil);
      setAutenticado(true);
    }
    return perfil;
  }

  const value = useMemo<AuthState>(
    () => ({ isAuthenticated: autenticado, eu, login, logout }),
    [autenticado, eu],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

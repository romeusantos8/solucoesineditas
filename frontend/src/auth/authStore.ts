// Contexto de autenticação (sem componentes nem hooks, para o fast-refresh do
// AuthProvider funcionar — ver AuthContext.tsx e useAuth.ts).
//
// Nome "authStore" (não "authContext") para não colidir com AuthContext.tsx no
// filesystem case-insensitive do Windows.

import { createContext } from "react";
import type { Eu, Perfil } from "../api/types";

export interface AuthState {
  isAuthenticated: boolean;
  // Quem está autenticado (GET /eu/). null enquanto carrega ou sem sessão.
  eu: Eu | null;
  login: (username: string, password: string) => Promise<Eu>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | undefined>(undefined);

// Página inicial de cada perfil: a gestão entra nos alertas; o funcionário
// no portal de despesas.
export function rotaInicial(perfil: Perfil): string {
  return perfil === "funcionario" ? "/minhas-despesas" : "/";
}

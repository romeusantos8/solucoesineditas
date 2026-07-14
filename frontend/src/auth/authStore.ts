// Contexto de autenticação (sem componentes nem hooks, para o fast-refresh do
// AuthProvider funcionar — ver AuthContext.tsx e useAuth.ts).
//
// Nome "authStore" (não "authContext") para não colidir com AuthContext.tsx no
// filesystem case-insensitive do Windows.

import { createContext } from "react";

export interface AuthState {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | undefined>(undefined);

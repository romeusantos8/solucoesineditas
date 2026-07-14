// Hook de conveniência para consumir o contexto de auth sem repetir o useContext.

import { useContext } from "react";
import { AuthContext } from "./authStore";

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth tem de ser usado dentro de <AuthProvider>.");
  }
  return ctx;
}

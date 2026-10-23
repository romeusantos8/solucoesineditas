// Envolve as rotas que exigem login. Sem sessão, manda para /login; com sessão
// de outro perfil (ex.: um funcionário a abrir /viaturas), manda para a página
// inicial desse perfil. A API recusa na mesma (403) — isto é só a navegação.

import { Navigate, Outlet } from "react-router-dom";
import type { Perfil } from "../api/types";
import { rotaInicial } from "../auth/authStore";
import { useAuth } from "../auth/useAuth";

export default function ProtectedRoute({ perfil }: { perfil: Perfil }) {
  const { isAuthenticated, eu } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!eu) return <p className="muted" style={{ padding: "2rem" }}>A carregar…</p>;
  if (eu.perfil !== perfil) return <Navigate to={rotaInicial(eu.perfil)} replace />;
  return <Outlet />;
}

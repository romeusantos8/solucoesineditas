// Envolve as rotas que exigem login. Se não houver sessão, manda para /login.

import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

export default function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

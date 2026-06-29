// Moldura comum das páginas autenticadas: barra de navegação + conteúdo.

import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="layout">
      <header className="navbar">
        <span className="navbar-brand">Gestão de Recursos</span>
        <nav className="navbar-links">
          <NavLink to="/">Alertas</NavLink>
          <NavLink to="/viaturas">Viaturas</NavLink>
          <NavLink to="/equipamentos">Equipamentos</NavLink>
        </nav>
        <button className="btn-link" onClick={handleLogout}>
          Terminar sessão
        </button>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}

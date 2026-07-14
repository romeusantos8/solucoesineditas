// Moldura da app autenticada: sidebar colapsável + topbar (com menu de
// utilizador) + área de conteúdo. A lógica de auth/routing fica intacta.

import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import logo from "../assets/logo-si.png";
import {
  IconeAlertas,
  IconeClientes,
  IconeEquipamentos,
  IconeFuncionarios,
  IconeMenu,
  IconeObras,
  IconeRelatorios,
  IconeSair,
  IconeViaturas,
} from "./Icones";

// Secções da navegação (rota, rótulo, ícone). `end` para a raiz não ficar
// sempre ativa.
const SECCOES = [
  { to: "/", rotulo: "Alertas", Icone: IconeAlertas, end: true },
  { to: "/viaturas", rotulo: "Viaturas", Icone: IconeViaturas },
  { to: "/equipamentos", rotulo: "Equipamentos", Icone: IconeEquipamentos },
  { to: "/funcionarios", rotulo: "Funcionários", Icone: IconeFuncionarios },
  { to: "/clientes", rotulo: "Clientes", Icone: IconeClientes },
  { to: "/obras", rotulo: "Obras", Icone: IconeObras },
  { to: "/relatorios", rotulo: "Relatórios", Icone: IconeRelatorios },
];

export default function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [colapsada, setColapsada] = useState(false);
  const [menuMobile, setMenuMobile] = useState(false);
  const [userAberto, setUserAberto] = useState(false);
  const userRef = useRef<HTMLDivElement>(null);

  // Fecha o menu de utilizador ao clicar fora.
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (userRef.current && !userRef.current.contains(e.target as Node)) {
        setUserAberto(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  // Fecha a sidebar mobile ao navegar.
  useEffect(() => setMenuMobile(false), [location.pathname]);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const tituloAtual =
    SECCOES.find((s) => (s.end ? location.pathname === s.to : location.pathname.startsWith(s.to)))
      ?.rotulo ?? "Gestão de Recursos";

  const classesShell = [
    "app-shell",
    colapsada ? "colapsada" : "",
    menuMobile ? "menu-aberto" : "",
  ].join(" ");

  return (
    <div className={classesShell}>
      {/* Backdrop em mobile quando a sidebar está aberta. */}
      {menuMobile && (
        <div className="backdrop-mobile so-mobile" onClick={() => setMenuMobile(false)} />
      )}

      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="logo">
            <img src={logo} alt="Soluções Inéditas" />
          </span>
          <span className="titulo">Gestão de Recursos</span>
        </div>

        <nav className="sidebar-nav">
          {SECCOES.map(({ to, rotulo, Icone, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className="sidebar-link"
              title={rotulo}
            >
              <span className="icone">
                <Icone />
              </span>
              <span className="rotulo">{rotulo}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <header className="topbar">
        {/* Colapsar (desktop) / abrir menu (mobile). */}
        <button
          className="icon-btn so-mobile"
          onClick={() => setMenuMobile((v) => !v)}
          aria-label="Abrir menu"
        >
          <IconeMenu />
        </button>
        <button
          className="icon-btn nao-mobile"
          onClick={() => setColapsada((v) => !v)}
          aria-label="Colapsar menu lateral"
        >
          <IconeMenu />
        </button>

        <span className="topbar-titulo">{tituloAtual}</span>
        <div className="topbar-spacer" />

        <div className="user-menu" ref={userRef}>
          <button
            className="user-trigger"
            onClick={() => setUserAberto((v) => !v)}
            aria-haspopup="menu"
            aria-expanded={userAberto}
          >
            <span className="avatar">SI</span>
          </button>
          {userAberto && (
            <div className="user-dropdown" role="menu">
              <button onClick={handleLogout} role="menuitem">
                <IconeSair />
                Terminar sessão
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

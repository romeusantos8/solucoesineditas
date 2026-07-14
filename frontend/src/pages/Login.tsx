// Página de login. Em sucesso, guarda o token e vai para o dashboard.

import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import logo from "../assets/logo-si.png";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [aGuardar, setAGuardar] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setAGuardar(true);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      // O DRF responde 400 quando as credenciais estão erradas.
      setErro("Credenciais inválidas. Tenta novamente.");
    } finally {
      setAGuardar(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <span className="login-logo">
          <img src={logo} alt="Soluções Inéditas" />
        </span>
        <h1>Gestão de Recursos</h1>
        <p className="muted">Soluções Inéditas — inicia sessão para continuar.</p>

        <form onSubmit={handleSubmit}>
          {erro && <div className="alert-erro">{erro}</div>}

          <label>
            Utilizador
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              required
            />
          </label>
          <label>
            Palavra-passe
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          <button type="submit" disabled={aGuardar}>
            {aGuardar ? "A entrar…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}

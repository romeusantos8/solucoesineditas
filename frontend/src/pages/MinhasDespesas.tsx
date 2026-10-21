// Portal do funcionário: o único ecrã que uma conta de funcionário vê.
//
// Pensado para o telemóvel: formulário curto (descrição, valor, data) no topo e
// as últimas despesas registadas por baixo. A despesa fica automaticamente no
// nome do funcionário autenticado (o backend ignora qualquer outro). Corrigir ou
// apagar uma despesa fica com o escritório, na app principal.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCrud } from "../api/useCrud";
import type { MinhaDespesa } from "../api/types";
import { useAuth } from "../auth/useAuth";
import CrudForm, { type Campo } from "../components/CrudForm";
import DataTable, { type Coluna } from "../components/DataTable";
import { IconeSair } from "../components/Icones";
import logo from "../assets/logo-si.png";

// Data de hoje em hora local (toISOString() daria a data UTC).
function hoje(): string {
  const d = new Date();
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mes}-${dia}`;
}

const colunas: Coluna<MinhaDespesa>[] = [
  { cabecalho: "Data", render: (d) => d.data },
  { cabecalho: "Descrição", render: (d) => d.descricao },
  { cabecalho: "Valor (€)", render: (d) => d.valor },
];

export default function MinhasDespesas() {
  const { eu, logout } = useAuth();
  const navigate = useNavigate();
  const despesas = useCrud<MinhaDespesa>("/minhas-despesas/");
  // Muda a cada registo para o formulário voltar a nascer vazio.
  const [versaoForm, setVersaoForm] = useState(0);
  const [registada, setRegistada] = useState(false);

  const campos: Campo[] = [
    { nome: "descricao", etiqueta: "Descrição (ex.: gasóleo, almoço, material)", obrigatorio: true },
    { nome: "valor", etiqueta: "Valor (€)", tipo: "number", obrigatorio: true },
    { nome: "data", etiqueta: "Data", tipo: "date", obrigatorio: true, padrao: hoje(), max: hoje() },
  ];

  async function registar(dados: Record<string, unknown>) {
    setRegistada(false);
    await despesas.criar(dados);
  }

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="portal">
      <header className="portal-topo">
        <span className="login-logo">
          <img src={logo} alt="Soluções Inéditas" />
        </span>
        <div className="portal-quem">
          <strong>{eu?.funcionario?.nome}</strong>
          <span className="muted">Registo de despesas</span>
        </div>
        <button className="btn-secundario" onClick={handleLogout}>
          <IconeSair />
          Sair
        </button>
      </header>

      <main className="portal-conteudo">
        <section className="card">
          <h2>Nova despesa</h2>
          {registada && <div className="alert-ok">Despesa registada.</div>}
          <CrudForm
            key={versaoForm}
            campos={campos}
            onSubmeter={registar}
            onSucesso={() => {
              setRegistada(true);
              setVersaoForm((v) => v + 1);
            }}
            textoBotao="Registar despesa"
          />
        </section>

        <section>
          <h2>As minhas despesas</h2>
          {despesas.erro && <div className="alert-erro">{despesas.erro}</div>}
          {!despesas.aCarregar && (
            <DataTable colunas={colunas} itens={despesas.itens} vazio="Ainda não registaste despesas." />
          )}
        </section>
      </main>
    </div>
  );
}

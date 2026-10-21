// Secção "Acesso à app" no detalhe de um funcionário: cria, altera ou revoga a
// conta com que ele entra no portal de despesas (POST/DELETE
// /funcionarios/{id}/acesso/). Essa conta só vê o registo das próprias despesas.
//
// Revogar desativa a conta (não a apaga); voltar a dar acesso reativa-a com a
// nova palavra-passe.

import { useState } from "react";
import { api } from "../api/client";
import type { Funcionario } from "../api/types";
import CrudForm, { type Campo } from "./CrudForm";
import Modal from "./Modal";

const campos: Campo[] = [
  { nome: "username", etiqueta: "Utilizador", obrigatorio: true },
  { nome: "password", etiqueta: "Palavra-passe (mín. 8 caracteres)", tipo: "password", obrigatorio: true },
];

interface Props {
  funcionario: Funcionario;
  onAlterado: (f: Funcionario) => void;
}

export default function AcessoAppSeccao({ funcionario, onAlterado }: Props) {
  const [aberto, setAberto] = useState(false);
  const acesso = funcionario.acesso;
  const ativo = Boolean(acesso?.ativo);
  const url = `/funcionarios/${funcionario.id}/acesso/`;

  async function guardar(dados: Record<string, unknown>) {
    const { data } = await api.post<Funcionario>(url, dados);
    onAlterado(data);
  }

  async function revogar() {
    if (!confirm(`Revogar o acesso de ${funcionario.nome} à app?`)) return;
    const { data } = await api.delete<Funcionario>(url);
    onAlterado(data);
  }

  return (
    <>
      <div className="acoes-header" style={{ marginTop: "2rem" }}>
        <h2>Acesso à app</h2>
        {/* Só funcionários ativos podem ter acesso (o portal recusa os outros). */}
        {funcionario.ativo && (
          <button onClick={() => setAberto(true)}>
            {ativo ? "Alterar palavra-passe" : "+ Dar acesso"}
          </button>
        )}
      </div>

      <div className="card">
        {ativo ? (
          <>
            <p>
              Entra com o utilizador <strong>{acesso?.username}</strong> e só vê o registo
              das suas despesas.
            </p>
            <button className="btn-link danger" onClick={revogar}>
              Revogar acesso
            </button>
          </>
        ) : acesso ? (
          <p className="muted">Acesso revogado (utilizador {acesso.username}).</p>
        ) : (
          <p className="muted">
            Sem acesso. Dá-lhe um utilizador e palavra-passe para registar as próprias despesas.
          </p>
        )}
      </div>

      <Modal
        aberto={aberto}
        titulo={ativo ? "Alterar palavra-passe" : "Dar acesso à app"}
        onFechar={() => setAberto(false)}
      >
        <CrudForm
          campos={campos}
          valoresIniciais={acesso ? { username: acesso.username } : {}}
          onSubmeter={guardar}
          onSucesso={() => setAberto(false)}
        />
      </Modal>
    </>
  );
}

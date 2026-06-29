// Lista e criação de equipamentos. CRUD mínimo: listar + criar + apagar.

import { useEffect, useState, type FormEvent } from "react";
import { AxiosError } from "axios";
import { api } from "../api/client";
import type { Equipamento, Paginated } from "../api/types";

function primeiraMensagemErro(err: unknown): string {
  if (err instanceof AxiosError && err.response?.status === 400) {
    const dados = err.response.data as Record<string, string[] | string>;
    const primeiro = Object.values(dados)[0];
    return Array.isArray(primeiro) ? primeiro[0] : String(primeiro);
  }
  return "Ocorreu um erro. Tenta novamente.";
}

export default function Equipamentos() {
  const [equipamentos, setEquipamentos] = useState<Equipamento[]>([]);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [nome, setNome] = useState("");
  const [numeroSerie, setNumeroSerie] = useState("");
  const [erroForm, setErroForm] = useState<string | null>(null);

  function carregar() {
    setACarregar(true);
    api
      .get<Paginated<Equipamento>>("/equipamentos/")
      .then((res) => setEquipamentos(res.data.results))
      .catch(() => setErro("Não foi possível carregar os equipamentos."))
      .finally(() => setACarregar(false));
  }

  useEffect(carregar, []);

  async function criar(e: FormEvent) {
    e.preventDefault();
    setErroForm(null);
    try {
      await api.post("/equipamentos/", {
        nome,
        // Nº de série é opcional; envia null se vazio (a API aceita).
        numero_serie: numeroSerie || null,
      });
      setNome("");
      setNumeroSerie("");
      carregar();
    } catch (err) {
      setErroForm(primeiraMensagemErro(err));
    }
  }

  async function apagar(id: number) {
    if (!confirm("Apagar este equipamento?")) return;
    try {
      await api.delete(`/equipamentos/${id}/`);
      carregar();
    } catch {
      alert("Não foi possível apagar (pode ter certificados associados).");
    }
  }

  return (
    <section>
      <h1>Equipamentos</h1>

      <form className="card form-inline" onSubmit={criar}>
        <h2>Novo equipamento</h2>
        {erroForm && <div className="alert-erro">{erroForm}</div>}
        <div className="form-row">
          <input
            placeholder="Nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
          />
          <input
            placeholder="Nº de série (opcional)"
            value={numeroSerie}
            onChange={(e) => setNumeroSerie(e.target.value)}
          />
          <button type="submit">Adicionar</button>
        </div>
      </form>

      {erro && <div className="alert-erro">{erro}</div>}
      {aCarregar ? (
        <p className="muted">A carregar…</p>
      ) : (
        <table className="tabela">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Nº de série</th>
              <th>Ativo</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {equipamentos.map((eq) => (
              <tr key={eq.id}>
                <td>{eq.nome}</td>
                <td>{eq.numero_serie ?? "—"}</td>
                <td>{eq.ativo ? "Sim" : "Não"}</td>
                <td>
                  <button className="btn-link danger" onClick={() => apagar(eq.id)}>
                    Apagar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

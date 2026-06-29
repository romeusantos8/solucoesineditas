// Lista e criação de viaturas. CRUD mínimo: listar + criar + apagar.

import { useEffect, useState, type FormEvent } from "react";
import { AxiosError } from "axios";
import { api } from "../api/client";
import type { Paginated, Viatura } from "../api/types";

// Extrai a primeira mensagem de erro de validação que o DRF devolver (400).
function primeiraMensagemErro(err: unknown): string {
  if (err instanceof AxiosError && err.response?.status === 400) {
    const dados = err.response.data as Record<string, string[] | string>;
    const primeiro = Object.values(dados)[0];
    return Array.isArray(primeiro) ? primeiro[0] : String(primeiro);
  }
  return "Ocorreu um erro. Tenta novamente.";
}

export default function Viaturas() {
  const [viaturas, setViaturas] = useState<Viatura[]>([]);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  // Formulário de nova viatura.
  const [matricula, setMatricula] = useState("");
  const [marca, setMarca] = useState("");
  const [modelo, setModelo] = useState("");
  const [ano, setAno] = useState("");
  const [erroForm, setErroForm] = useState<string | null>(null);

  function carregar() {
    setACarregar(true);
    api
      .get<Paginated<Viatura>>("/viaturas/")
      .then((res) => setViaturas(res.data.results))
      .catch(() => setErro("Não foi possível carregar as viaturas."))
      .finally(() => setACarregar(false));
  }

  useEffect(carregar, []);

  async function criar(e: FormEvent) {
    e.preventDefault();
    setErroForm(null);
    try {
      await api.post("/viaturas/", {
        matricula,
        marca,
        modelo,
        ano: ano ? Number(ano) : null,
      });
      setMatricula("");
      setMarca("");
      setModelo("");
      setAno("");
      carregar();
    } catch (err) {
      setErroForm(primeiraMensagemErro(err));
    }
  }

  async function apagar(id: number) {
    if (!confirm("Apagar esta viatura?")) return;
    try {
      await api.delete(`/viaturas/${id}/`);
      carregar();
    } catch {
      // PROTECT no backend impede apagar viaturas com histórico associado.
      alert("Não foi possível apagar (pode ter seguros/inspeções associados).");
    }
  }

  return (
    <section>
      <h1>Viaturas</h1>

      <form className="card form-inline" onSubmit={criar}>
        <h2>Nova viatura</h2>
        {erroForm && <div className="alert-erro">{erroForm}</div>}
        <div className="form-row">
          <input
            placeholder="Matrícula"
            value={matricula}
            onChange={(e) => setMatricula(e.target.value)}
            required
          />
          <input
            placeholder="Marca"
            value={marca}
            onChange={(e) => setMarca(e.target.value)}
            required
          />
          <input
            placeholder="Modelo"
            value={modelo}
            onChange={(e) => setModelo(e.target.value)}
            required
          />
          <input
            placeholder="Ano"
            type="number"
            value={ano}
            onChange={(e) => setAno(e.target.value)}
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
              <th>Matrícula</th>
              <th>Marca</th>
              <th>Modelo</th>
              <th>Ano</th>
              <th>Ativa</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {viaturas.map((v) => (
              <tr key={v.id}>
                <td>{v.matricula}</td>
                <td>{v.marca}</td>
                <td>{v.modelo}</td>
                <td>{v.ano ?? "—"}</td>
                <td>{v.ativa ? "Sim" : "Não"}</td>
                <td>
                  <button className="btn-link danger" onClick={() => apagar(v.id)}>
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

// Lista e criação de equipamentos. Cada equipamento pode ter um funcionário
// responsável (select carregado da API).

import { useState } from "react";
import { Link } from "react-router-dom";
import { useCrud } from "../api/useCrud";
import { useOpcoes } from "../api/useOpcoes";
import BotaoEditar from "../components/BotaoEditar";
import DataTable, { type Coluna } from "../components/DataTable";
import Dica from "../components/Dica";
import ModalForm from "../components/ModalForm";
import { type Campo } from "../components/CrudForm";
import type { Equipamento, Funcionario } from "../api/types";

const colunas: Coluna<Equipamento>[] = [
  // O nome liga ao detalhe do equipamento (certificados).
  { cabecalho: "Nome", render: (e) => <Link to={`/equipamentos/${e.id}`}>{e.nome}</Link> },
  { cabecalho: "Nº de série", render: (e) => e.numero_serie ?? "—" },
  { cabecalho: "Responsável", render: (e) => e.responsavel_nome ?? "—" },
  { cabecalho: "Ativo", render: (e) => (e.ativo ? "Sim" : "Não") },
];

export default function Equipamentos() {
  // Filtro por responsável (vazio = todos). Passa como ?responsavel=ID à API.
  const [filtroResponsavel, setFiltroResponsavel] = useState<string>("");
  const query = filtroResponsavel ? `?responsavel=${filtroResponsavel}` : "";

  const { itens, aCarregar, erro, criar, editar, apagar } =
    useCrud<Equipamento>("/equipamentos/", query);
  // Só funcionários ativos podem ser NOVOS responsáveis (no formulário).
  const funcionarios = useOpcoes<Funcionario>("/funcionarios/?ativo=true", (f) => f.nome);
  // No filtro mostramos TODOS (incluindo inativos): um equipamento pode ter
  // como responsável alguém que entretanto saiu, e queremos poder filtrá-lo.
  const todosFuncionarios = useOpcoes<Funcionario>("/funcionarios/", (f) => f.nome);

  const campos: Campo[] = [
    { nome: "nome", etiqueta: "Nome", obrigatorio: true },
    { nome: "numero_serie", etiqueta: "Nº de série (opcional)", vazioComoNull: true },
    { nome: "responsavel", etiqueta: "Responsável (opcional)", opcoes: funcionarios },
    {
      nome: "ativo",
      etiqueta: "Estado",
      obrigatorio: true,
      padrao: "true",
      opcoes: [
        { valor: "true", texto: "Ativo" },
        { valor: "false", texto: "Inativo" },
      ],
    },
  ];

  async function confirmarApagar(e: Equipamento) {
    if (!confirm("Apagar este equipamento?")) return;
    try {
      await apagar(e.id);
    } catch {
      alert("Não foi possível apagar (pode ter certificados associados).");
    }
  }

  return (
    <section>
      <div className="acoes-header">
        <h1>Equipamentos</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          <label className="filtro">
            Responsável
            <select
              value={filtroResponsavel}
              onChange={(e) => setFiltroResponsavel(e.target.value)}
            >
              <option value="">Todos</option>
              {todosFuncionarios.map((f) => (
                <option key={f.valor} value={f.valor}>{f.texto}</option>
              ))}
            </select>
          </label>
          <ModalForm textoBotao="+ Novo equipamento" titulo="Novo equipamento" campos={campos} onCriar={criar} />
        </div>
      </div>
      {erro && <div className="alert-erro">{erro}</div>}
      <Dica>
        Clica no <strong>nome</strong> de um equipamento para ver os detalhes e
        adicionar certificados.
      </Dica>
      {aCarregar ? (
        <p className="muted">A carregar…</p>
      ) : (
        <DataTable
          colunas={colunas}
          itens={itens}
          acoes={(e) => (
            <BotaoEditar item={e} titulo="Editar equipamento" campos={campos} onEditar={editar} />
          )}
          onApagar={confirmarApagar}
        />
      )}
    </section>
  );
}

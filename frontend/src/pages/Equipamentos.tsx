// Lista e criação de equipamentos. Cada equipamento pode ter um funcionário
// responsável (select carregado da API).

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
  const { itens, aCarregar, erro, criar, editar, apagar } =
    useCrud<Equipamento>("/equipamentos/");
  // Só funcionários ativos podem ser responsáveis.
  const funcionarios = useOpcoes<Funcionario>("/funcionarios/?ativo=true", (f) => f.nome);

  const campos: Campo[] = [
    { nome: "nome", etiqueta: "Nome", obrigatorio: true },
    { nome: "numero_serie", etiqueta: "Nº de série (opcional)", vazioComoNull: true },
    { nome: "responsavel", etiqueta: "Responsável (opcional)", opcoes: funcionarios },
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
        <ModalForm textoBotao="+ Novo equipamento" titulo="Novo equipamento" campos={campos} onCriar={criar} />
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

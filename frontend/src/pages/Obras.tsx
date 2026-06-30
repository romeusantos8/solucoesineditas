// Lista e criação de obras. O formulário tem um select de cliente (carregado da
// API) e o estado. Cada obra liga ao seu detalhe (alocações).

import { Link } from "react-router-dom";
import { useCrud } from "../api/useCrud";
import { useOpcoes } from "../api/useOpcoes";
import { type Campo } from "../components/CrudForm";
import BotaoEditar from "../components/BotaoEditar";
import DataTable, { type Coluna } from "../components/DataTable";
import ModalForm from "../components/ModalForm";
import type { Cliente, EstadoObra, Obra } from "../api/types";

const ESTADOS: { valor: EstadoObra; texto: string }[] = [
  { valor: "planeada", texto: "Planeada" },
  { valor: "em_curso", texto: "Em curso" },
  { valor: "concluida", texto: "Concluída" },
  { valor: "cancelada", texto: "Cancelada" },
];

const colunas: Coluna<Obra>[] = [
  { cabecalho: "Nome", render: (o) => <Link to={`/obras/${o.id}`}>{o.nome}</Link> },
  {
    cabecalho: "Estado",
    render: (o) => ESTADOS.find((e) => e.valor === o.estado)?.texto ?? o.estado,
  },
  { cabecalho: "Início", render: (o) => o.data_inicio },
  { cabecalho: "Fim previsto", render: (o) => o.data_fim_prevista ?? "—" },
  {
    cabecalho: "Alocados",
    render: (o) =>
      `${o.alocacoes_funcionarios.length} func. / ${o.alocacoes_equipamentos.length} equip.`,
  },
];

export default function Obras() {
  const { itens, aCarregar, erro, criar, editar, apagar } = useCrud<Obra>("/obras/");
  const clientes = useOpcoes<Cliente>("/clientes/", (c) => c.nome);

  const campos: Campo[] = [
    { nome: "cliente", etiqueta: "Cliente", obrigatorio: true, opcoes: clientes },
    { nome: "nome", etiqueta: "Nome da obra", obrigatorio: true },
    { nome: "data_inicio", etiqueta: "Data de início", tipo: "date", obrigatorio: true },
    { nome: "data_fim_prevista", etiqueta: "Fim previsto (opcional)", tipo: "date" },
    { nome: "estado", etiqueta: "Estado", opcoes: ESTADOS },
  ];

  async function confirmarApagar(o: Obra) {
    if (!confirm("Apagar esta obra?")) return;
    try {
      await apagar(o.id);
    } catch {
      alert("Não foi possível apagar (pode ter alocações associadas).");
    }
  }

  return (
    <section>
      <div className="acoes-header">
        <h1>Obras</h1>
        <ModalForm textoBotao="+ Nova obra" titulo="Nova obra" campos={campos} onCriar={criar} />
      </div>
      {erro && <div className="alert-erro">{erro}</div>}
      {aCarregar ? (
        <p className="muted">A carregar…</p>
      ) : (
        <DataTable
          colunas={colunas}
          itens={itens}
          acoes={(o) => (
            <BotaoEditar item={o} titulo="Editar obra" campos={campos} onEditar={editar} />
          )}
          onApagar={confirmarApagar}
        />
      )}
    </section>
  );
}

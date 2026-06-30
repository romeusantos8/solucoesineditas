// Lista e criação de viaturas, sobre os componentes genéricos de CRUD.

import { Link } from "react-router-dom";
import CrudPage from "../components/CrudPage";
import type { Coluna } from "../components/DataTable";
import type { Campo } from "../components/CrudForm";
import type { Viatura } from "../api/types";

const campos: Campo[] = [
  { nome: "matricula", etiqueta: "Matrícula", obrigatorio: true },
  { nome: "marca", etiqueta: "Marca", obrigatorio: true },
  { nome: "modelo", etiqueta: "Modelo", obrigatorio: true },
  { nome: "ano", etiqueta: "Ano", tipo: "number" },
];

const colunas: Coluna<Viatura>[] = [
  // A matrícula liga ao detalhe da viatura (seguros, inspeções, despesas).
  { cabecalho: "Matrícula", render: (v) => <Link to={`/viaturas/${v.id}`}>{v.matricula}</Link> },
  { cabecalho: "Marca", render: (v) => v.marca },
  { cabecalho: "Modelo", render: (v) => v.modelo },
  { cabecalho: "Ano", render: (v) => v.ano ?? "—" },
  { cabecalho: "Ativa", render: (v) => (v.ativa ? "Sim" : "Não") },
];

export default function Viaturas() {
  return (
    <CrudPage<Viatura>
      titulo="Viaturas"
      recurso="/viaturas/"
      tituloForm="Nova viatura"
      campos={campos}
      colunas={colunas}
      avisoApagar="Não foi possível apagar (pode ter seguros/inspeções associados)."
    />
  );
}

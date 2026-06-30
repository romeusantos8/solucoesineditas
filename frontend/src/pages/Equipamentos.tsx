// Lista e criação de equipamentos, sobre os componentes genéricos de CRUD.

import { Link } from "react-router-dom";
import CrudPage from "../components/CrudPage";
import type { Coluna } from "../components/DataTable";
import type { Campo } from "../components/CrudForm";
import type { Equipamento } from "../api/types";

const campos: Campo[] = [
  { nome: "nome", etiqueta: "Nome", obrigatorio: true },
  { nome: "numero_serie", etiqueta: "Nº de série (opcional)", vazioComoNull: true },
];

const colunas: Coluna<Equipamento>[] = [
  // O nome liga ao detalhe do equipamento (certificados).
  { cabecalho: "Nome", render: (e) => <Link to={`/equipamentos/${e.id}`}>{e.nome}</Link> },
  { cabecalho: "Nº de série", render: (e) => e.numero_serie ?? "—" },
  { cabecalho: "Ativo", render: (e) => (e.ativo ? "Sim" : "Não") },
];

export default function Equipamentos() {
  return (
    <CrudPage<Equipamento>
      titulo="Equipamentos"
      recurso="/equipamentos/"
      tituloForm="Novo equipamento"
      campos={campos}
      colunas={colunas}
      avisoApagar="Não foi possível apagar (pode ter certificados associados)."
    />
  );
}

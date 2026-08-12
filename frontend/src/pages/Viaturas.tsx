// Lista e criação de viaturas, sobre os componentes genéricos de CRUD.

import { Link } from "react-router-dom";
import CrudPage from "../components/CrudPage";
import { useOpcoes } from "../api/useOpcoes";
import type { Coluna } from "../components/DataTable";
import type { Campo } from "../components/CrudForm";
import type { Viatura, Funcionario } from "../api/types";

const colunas: Coluna<Viatura>[] = [
  // A matrícula liga ao detalhe da viatura (seguros, inspeções, despesas).
  { cabecalho: "Matrícula", render: (v) => <Link to={`/viaturas/${v.id}`}>{v.matricula}</Link> },
  { cabecalho: "Marca", render: (v) => v.marca },
  { cabecalho: "Modelo", render: (v) => v.modelo },
  { cabecalho: "Ano", render: (v) => v.ano ?? "—" },
  { cabecalho: "Responsável", render: (v) => v.responsavel_nome ?? "—" },
  { cabecalho: "Ativa", render: (v) => (v.ativa ? "Sim" : "Não") },
];

export default function Viaturas() {
  // Select do responsável: só funcionários ativos (mesmo padrão dos equipamentos).
  const funcionarios = useOpcoes<Funcionario>("/funcionarios/?ativo=true", (f) => f.nome);

  const campos: Campo[] = [
    { nome: "matricula", etiqueta: "Matrícula", obrigatorio: true },
    { nome: "marca", etiqueta: "Marca", obrigatorio: true },
    { nome: "modelo", etiqueta: "Modelo", obrigatorio: true },
    { nome: "ano", etiqueta: "Ano", tipo: "number" },
    { nome: "responsavel", etiqueta: "Responsável (opcional)", opcoes: funcionarios },
    // Estado da viatura (ativa/abatida). Obrigatório; nova viatura = ativa.
    {
      nome: "ativa",
      etiqueta: "Estado",
      obrigatorio: true,
      padrao: "true",
      opcoes: [
        { valor: "true", texto: "Ativa" },
        { valor: "false", texto: "Inativa" },
      ],
    },
  ];

  return (
    <CrudPage<Viatura>
      titulo="Viaturas"
      recurso="/viaturas/"
      tituloForm="Nova viatura"
      campos={campos}
      colunas={colunas}
      dica={<>Clica na <strong>matrícula</strong> de uma viatura para ver seguros, inspeções e despesas.</>}
      avisoApagar="Não foi possível apagar (pode ter seguros/inspeções associados)."
    />
  );
}

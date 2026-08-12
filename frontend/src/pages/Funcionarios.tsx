// Lista e criação de funcionários.

import { Link } from "react-router-dom";
import CrudPage from "../components/CrudPage";
import type { Coluna } from "../components/DataTable";
import type { Campo } from "../components/CrudForm";
import type { Funcionario } from "../api/types";

const OPCOES_ATIVO = [
  { valor: "true", texto: "Ativo" },
  { valor: "false", texto: "Inativo" },
];

const campos: Campo[] = [
  { nome: "nome", etiqueta: "Nome", obrigatorio: true },
  { nome: "funcao", etiqueta: "Função", obrigatorio: true },
  { nome: "data_admissao", etiqueta: "Data de admissão", tipo: "date", obrigatorio: true },
  { nome: "nif", etiqueta: "NIF (opcional)", vazioComoNull: true },
  { nome: "email", etiqueta: "Email (opcional)", tipo: "email" },
  { nome: "telefone", etiqueta: "Telefone (opcional)" },
  // Estado do funcionário (ex.: suspender/reativar). Obrigatório: sempre um dos
  // dois valores, nunca vazio.
  { nome: "ativo", etiqueta: "Estado", opcoes: OPCOES_ATIVO, obrigatorio: true, padrao: "true" },
];

const colunas: Coluna<Funcionario>[] = [
  { cabecalho: "Nome", render: (f) => <Link to={`/funcionarios/${f.id}`}>{f.nome}</Link> },
  { cabecalho: "Função", render: (f) => f.funcao },
  { cabecalho: "NIF", render: (f) => f.nif ?? "—" },
  { cabecalho: "Admissão", render: (f) => f.data_admissao },
  { cabecalho: "Ativo", render: (f) => (f.ativo ? "Sim" : "Não") },
];

export default function Funcionarios() {
  return (
    <CrudPage<Funcionario>
      titulo="Funcionários"
      recurso="/funcionarios/"
      tituloForm="Novo funcionário"
      campos={campos}
      colunas={colunas}
      dica={<>Clica no <strong>nome</strong> de um funcionário para ver despesas e a ficha médica.</>}
      avisoApagar="Não foi possível apagar (pode ter despesas ou alocações associadas)."
    />
  );
}

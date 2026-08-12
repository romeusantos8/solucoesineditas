// Lista e criação de clientes.

import CrudPage from "../components/CrudPage";
import type { Coluna } from "../components/DataTable";
import type { Campo } from "../components/CrudForm";
import type { Cliente } from "../api/types";

const campos: Campo[] = [
  { nome: "nome", etiqueta: "Nome", obrigatorio: true },
  { nome: "nif", etiqueta: "NIF (opcional)", vazioComoNull: true },
  { nome: "email", etiqueta: "Email (opcional)", tipo: "email" },
  { nome: "telefone", etiqueta: "Telefone (opcional)" },
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

const colunas: Coluna<Cliente>[] = [
  { cabecalho: "Nome", render: (c) => c.nome },
  { cabecalho: "NIF", render: (c) => c.nif ?? "—" },
  { cabecalho: "Email", render: (c) => c.email || "—" },
  { cabecalho: "Telefone", render: (c) => c.telefone || "—" },
  { cabecalho: "Ativo", render: (c) => (c.ativo ? "Sim" : "Não") },
];

export default function Clientes() {
  return (
    <CrudPage<Cliente>
      titulo="Clientes"
      recurso="/clientes/"
      tituloForm="Novo cliente"
      campos={campos}
      colunas={colunas}
      avisoApagar="Não foi possível apagar (pode ter obras associadas)."
    />
  );
}

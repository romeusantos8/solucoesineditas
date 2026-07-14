// Detalhe de um funcionário: despesas associadas.

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useCrud } from "../api/useCrud";
import { type Campo } from "../components/CrudForm";
import BotaoEditar from "../components/BotaoEditar";
import BotaoVoltar from "../components/BotaoVoltar";
import DataTable, { type Coluna } from "../components/DataTable";
import ModalForm from "../components/ModalForm";
import FichaMedicaSeccao from "../components/FichaMedicaSeccao";
import type { DespesaFuncionario, Funcionario } from "../api/types";

export default function FuncionarioDetalhe() {
  const { id } = useParams<{ id: string }>();
  const funcId = Number(id);
  const [func, setFunc] = useState<Funcionario | null>(null);

  useEffect(() => {
    api.get<Funcionario>(`/funcionarios/${funcId}/`).then((res) => setFunc(res.data));
  }, [funcId]);

  const despesas = useCrud<DespesaFuncionario>(
    "/despesas-funcionarios/",
    `?funcionario=${funcId}`,
  );

  if (!func) return <p className="muted">A carregar…</p>;

  const campos: Campo[] = [
    { nome: "descricao", etiqueta: "Descrição", obrigatorio: true },
    { nome: "valor", etiqueta: "Valor (€)", tipo: "number", obrigatorio: true },
    { nome: "data", etiqueta: "Data", tipo: "date", obrigatorio: true },
  ];
  const colunas: Coluna<DespesaFuncionario>[] = [
    { cabecalho: "Descrição", render: (d) => d.descricao },
    { cabecalho: "Valor (€)", render: (d) => d.valor },
    { cabecalho: "Data", render: (d) => d.data },
  ];

  const criar = (dados: Record<string, unknown>) =>
    despesas.criar({ ...dados, funcionario: funcId });

  return (
    <section>
      <BotaoVoltar para="/funcionarios" />
      <h1>{func.nome}</h1>
      <p className="muted">{func.funcao}{func.nif ? ` · NIF ${func.nif}` : ""}</p>

      <div className="acoes-header">
        <h2>Despesas</h2>
        <ModalForm textoBotao="+ Nova despesa" titulo="Nova despesa" campos={campos} onCriar={criar} />
      </div>
      <DataTable
        colunas={colunas}
        itens={despesas.itens}
        acoes={(d) => <BotaoEditar item={d} titulo="Editar despesa" campos={campos} onEditar={despesas.editar} />}
        onApagar={(d) => despesas.apagar(d.id)}
        vazio="Sem despesas."
      />

      {/* Dados de saúde (RGPD): a secção esconde-se se o utilizador não tiver
          acesso (403). */}
      <FichaMedicaSeccao funcionarioId={funcId} />
    </section>
  );
}

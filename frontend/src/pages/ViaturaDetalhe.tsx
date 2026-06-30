// Detalhe de uma viatura: seguros, inspeções e despesas associadas.

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useCrud } from "../api/useCrud";
import { type Campo } from "../components/CrudForm";
import BotaoEditar from "../components/BotaoEditar";
import DataTable, { type Coluna } from "../components/DataTable";
import ModalForm from "../components/ModalForm";
import type {
  DespesaViatura,
  Inspecao,
  SeguroViatura,
  Viatura,
} from "../api/types";

export default function ViaturaDetalhe() {
  const { id } = useParams<{ id: string }>();
  const viaturaId = Number(id);
  const [viatura, setViatura] = useState<Viatura | null>(null);

  useEffect(() => {
    api.get<Viatura>(`/viaturas/${viaturaId}/`).then((res) => setViatura(res.data));
  }, [viaturaId]);

  const seguros = useCrud<SeguroViatura>("/seguros/", `?viatura=${viaturaId}`);
  const inspecoes = useCrud<Inspecao>("/inspecoes/", `?viatura=${viaturaId}`);
  const despesas = useCrud<DespesaViatura>("/despesas/", `?viatura=${viaturaId}`);

  if (!viatura) return <p className="muted">A carregar…</p>;

  const camposSeguro: Campo[] = [
    { nome: "seguradora", etiqueta: "Seguradora", obrigatorio: true },
    { nome: "apolice", etiqueta: "Nº apólice", obrigatorio: true },
    { nome: "data_inicio", etiqueta: "Início", tipo: "date", obrigatorio: true },
    { nome: "data_validade", etiqueta: "Validade", tipo: "date", obrigatorio: true },
  ];
  const camposInspecao: Campo[] = [
    { nome: "data_inspecao", etiqueta: "Data inspeção", tipo: "date", obrigatorio: true },
    { nome: "data_validade", etiqueta: "Validade", tipo: "date", obrigatorio: true },
    {
      nome: "resultado",
      etiqueta: "Resultado",
      opcoes: [
        { valor: "aprovado", texto: "Aprovado" },
        { valor: "reprovado", texto: "Reprovado" },
      ],
    },
  ];
  const camposDespesa: Campo[] = [
    { nome: "descricao", etiqueta: "Descrição", obrigatorio: true },
    { nome: "valor", etiqueta: "Valor (€)", tipo: "number", obrigatorio: true },
    { nome: "data", etiqueta: "Data", tipo: "date", obrigatorio: true },
  ];

  const colSeguro: Coluna<SeguroViatura>[] = [
    { cabecalho: "Seguradora", render: (s) => s.seguradora },
    { cabecalho: "Apólice", render: (s) => s.apolice },
    { cabecalho: "Validade", render: (s) => s.data_validade },
    { cabecalho: "Dias", render: (s) => s.dias_para_expirar },
  ];
  const colInspecao: Coluna<Inspecao>[] = [
    { cabecalho: "Data", render: (i) => i.data_inspecao },
    { cabecalho: "Validade", render: (i) => i.data_validade },
    { cabecalho: "Resultado", render: (i) => i.resultado },
  ];
  const colDespesa: Coluna<DespesaViatura>[] = [
    { cabecalho: "Descrição", render: (d) => d.descricao },
    { cabecalho: "Valor (€)", render: (d) => d.valor },
    { cabecalho: "Data", render: (d) => d.data },
  ];

  const comViatura = (criar: (d: Record<string, unknown>) => Promise<void>) =>
    (dados: Record<string, unknown>) => criar({ ...dados, viatura: viaturaId });

  return (
    <section>
      <h1>{viatura.matricula}</h1>
      <p className="muted">{viatura.marca} {viatura.modelo}</p>

      <div className="acoes-header">
        <h2>Seguros</h2>
        <ModalForm textoBotao="+ Novo seguro" titulo="Novo seguro" campos={camposSeguro} onCriar={comViatura(seguros.criar)} />
      </div>
      <DataTable
        colunas={colSeguro}
        itens={seguros.itens}
        acoes={(s) => <BotaoEditar item={s} titulo="Editar seguro" campos={camposSeguro} onEditar={seguros.editar} />}
        onApagar={(s) => seguros.apagar(s.id)}
        vazio="Sem seguros."
      />

      <div className="acoes-header" style={{ marginTop: "2rem" }}>
        <h2>Inspeções</h2>
        <ModalForm textoBotao="+ Nova inspeção" titulo="Nova inspeção" campos={camposInspecao} onCriar={comViatura(inspecoes.criar)} />
      </div>
      <DataTable
        colunas={colInspecao}
        itens={inspecoes.itens}
        acoes={(i) => <BotaoEditar item={i} titulo="Editar inspeção" campos={camposInspecao} onEditar={inspecoes.editar} />}
        onApagar={(i) => inspecoes.apagar(i.id)}
        vazio="Sem inspeções."
      />

      <div className="acoes-header" style={{ marginTop: "2rem" }}>
        <h2>Despesas</h2>
        <ModalForm textoBotao="+ Nova despesa" titulo="Nova despesa" campos={camposDespesa} onCriar={comViatura(despesas.criar)} />
      </div>
      <DataTable
        colunas={colDespesa}
        itens={despesas.itens}
        acoes={(d) => <BotaoEditar item={d} titulo="Editar despesa" campos={camposDespesa} onEditar={despesas.editar} />}
        onApagar={(d) => despesas.apagar(d.id)}
        vazio="Sem despesas."
      />
    </section>
  );
}

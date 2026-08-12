// Detalhe de uma obra: dados + alocação de funcionários. Os equipamentos da obra
// são DERIVADOS (os dos funcionários alocados) e mostrados em lista só-leitura.

import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useCrud } from "../api/useCrud";
import { useOpcoes } from "../api/useOpcoes";
import { type Campo } from "../components/CrudForm";
import BotaoEditar from "../components/BotaoEditar";
import BotaoVoltar from "../components/BotaoVoltar";
import DataTable, { type Coluna } from "../components/DataTable";
import ModalForm from "../components/ModalForm";
import type {
  AlocacaoFuncionario,
  AutoObra,
  EquipamentoDerivado,
  Funcionario,
  Obra,
} from "../api/types";

export default function ObraDetalhe() {
  const { id } = useParams<{ id: string }>();
  const obraId = Number(id);

  const [obra, setObra] = useState<Obra | null>(null);

  const carregarObra = useCallback(() => {
    api.get<Obra>(`/obras/${obraId}/`).then((res) => setObra(res.data));
  }, [obraId]);

  useEffect(carregarObra, [carregarObra]);

  // Alocações de funcionários desta obra; recarregam ao alocar/desalocar.
  const aFunc = useCrud<AlocacaoFuncionario>(
    "/alocacoes-funcionarios/",
    `?obra=${obraId}`,
  );

  const funcionarios = useOpcoes<Funcionario>("/funcionarios/?ativo=true", (f) => f.nome);

  // Autos mensais (faturação) desta obra.
  const autos = useCrud<AutoObra>("/autos-obras/", `?obra=${obraId}`);

  if (!obra) return <p className="muted">A carregar…</p>;

  // O auto guarda ano+mes separados no backend, mas na UI usamos UM seletor de
  // mês (<input type="month">, valor "AAAA-MM"). Estas funções convertem entre
  // os dois formatos.
  const periodoParaAnoMes = (periodo: string): { ano: number; mes: number } => {
    const [ano, mes] = periodo.split("-");
    return { ano: Number(ano), mes: Number(mes) };
  };
  const anoMesParaPeriodo = (ano: number, mes: number): string =>
    `${ano}-${String(mes).padStart(2, "0")}`;

  const camposAuto: Campo[] = [
    { nome: "periodo", etiqueta: "Mês", tipo: "month", obrigatorio: true },
    { nome: "valor", etiqueta: "Valor (€)", tipo: "number", obrigatorio: true },
    { nome: "descricao", etiqueta: "Descrição (opcional)" },
    {
      nome: "estado",
      etiqueta: "Estado",
      obrigatorio: true,
      padrao: "por_faturar",
      opcoes: [
        { valor: "por_faturar", texto: "Por faturar" },
        { valor: "faturado", texto: "Faturado" },
      ],
    },
  ];

  const colAuto: Coluna<AutoObra>[] = [
    { cabecalho: "Período", render: (a) => `${String(a.mes).padStart(2, "0")}/${a.ano}` },
    { cabecalho: "Valor (€)", render: (a) => a.valor },
    { cabecalho: "Estado", render: (a) => a.estado_display },
    { cabecalho: "Descrição", render: (a) => a.descricao || "—" },
  ];

  // Total faturado da obra (só autos no estado "faturado"), para mostrar no topo
  // da secção sem um pedido extra ao relatório.
  const totalFaturado = autos.itens
    .filter((a) => a.estado === "faturado")
    .reduce((soma, a) => soma + Number(a.valor), 0);

  // Converte o campo `periodo` ("AAAA-MM") em ano+mes antes de enviar à API.
  function comAnoMes(dados: Record<string, unknown>): Record<string, unknown> {
    const { periodo, ...resto } = dados;
    if (typeof periodo === "string" && periodo) {
      return { ...resto, ...periodoParaAnoMes(periodo) };
    }
    return resto;
  }

  async function criarAuto(dados: Record<string, unknown>) {
    await autos.criar({ ...comAnoMes(dados), obra: obraId });
  }
  async function editarAuto(id: number, dados: Record<string, unknown>) {
    await autos.editar(id, comAnoMes(dados));
  }

  // A data de fim de uma alocação não pode ultrapassar o fim previsto da obra.
  const maxFim = obra.data_fim_prevista ?? undefined;

  const camposFunc: Campo[] = [
    { nome: "funcionario", etiqueta: "Funcionário", obrigatorio: true, opcoes: funcionarios },
    { nome: "data_inicio", etiqueta: "Início", tipo: "date", obrigatorio: true },
    { nome: "data_fim", etiqueta: "Fim (opcional)", tipo: "date", max: maxFim },
  ];
  // Na edição de uma alocação só se mexem as datas (não se troca o funcionário).
  const camposEditarDatas: Campo[] = [
    { nome: "data_inicio", etiqueta: "Início", tipo: "date", obrigatorio: true },
    { nome: "data_fim", etiqueta: "Fim (opcional)", tipo: "date", max: maxFim },
  ];

  const colFunc: Coluna<AlocacaoFuncionario>[] = [
    { cabecalho: "Funcionário", render: (a) => a.funcionario_nome },
    { cabecalho: "Início", render: (a) => a.data_inicio },
    { cabecalho: "Fim", render: (a) => a.data_fim ?? "—" },
  ];
  const colEquip: Coluna<EquipamentoDerivado & { id: number }>[] = [
    { cabecalho: "Equipamento", render: (e) => e.nome },
    { cabecalho: "Nº de série", render: (e) => e.numero_serie ?? "—" },
    { cabecalho: "Via funcionário", render: (e) => e.funcionario_nome },
  ];

  // Ao criar/remover alocação, injeta a obra e recarrega a obra (para os
  // equipamentos derivados refletirem os funcionários atuais).
  async function criarFunc(dados: Record<string, unknown>) {
    await aFunc.criar({ ...dados, obra: obraId });
    carregarObra();
  }
  async function editarFunc(id: number, dados: Record<string, unknown>) {
    await aFunc.editar(id, dados);
    carregarObra();
  }
  async function desalocarFunc(id: number) {
    if (!confirm("Remover esta alocação?")) return;
    await aFunc.apagar(id);
    carregarObra();
  }

  return (
    <section>
      <BotaoVoltar para="/obras" />
      <h1>{obra.nome}</h1>
      <p className="muted">
        Início: {obra.data_inicio}
        {obra.data_fim_prevista ? ` · Fim previsto: ${obra.data_fim_prevista}` : ""}
      </p>

      <div className="acoes-header">
        <h2>Funcionários alocados</h2>
        <ModalForm textoBotao="+ Alocar funcionário" titulo="Alocar funcionário" campos={camposFunc} onCriar={criarFunc} />
      </div>
      <DataTable
        colunas={colFunc}
        itens={aFunc.itens}
        acoes={(a) => (
          <BotaoEditar item={a} titulo="Editar alocação" campos={camposEditarDatas} onEditar={editarFunc} />
        )}
        onApagar={(a) => desalocarFunc(a.id)}
        vazio="Nenhum funcionário alocado."
      />

      <div className="acoes-header" style={{ marginTop: "2rem" }}>
        <h2>Autos mensais (faturação)</h2>
        <ModalForm textoBotao="+ Novo auto" titulo="Novo auto mensal" campos={camposAuto} onCriar={criarAuto} />
      </div>
      <p className="muted" style={{ marginBottom: "0.75rem" }}>
        Total já faturado: <strong>{totalFaturado.toFixed(2)} €</strong>
      </p>
      {autos.erro && <div className="alert-erro">{autos.erro}</div>}
      <DataTable
        colunas={colAuto}
        itens={autos.itens}
        acoes={(a) => (
          <BotaoEditar
            // `periodo` (AAAA-MM) derivado do ano+mes, para o seletor de mês
            // vir pré-preenchido na edição.
            item={{ ...a, periodo: anoMesParaPeriodo(a.ano, a.mes) }}
            titulo="Editar auto"
            campos={camposAuto}
            onEditar={editarAuto}
          />
        )}
        onApagar={(a) => {
          if (confirm("Apagar este auto?")) autos.apagar(a.id);
        }}
        vazio="Sem autos registados."
      />

      <h2 style={{ marginTop: "2rem" }}>Equipamentos na obra</h2>
      <p className="muted" style={{ marginBottom: "0.75rem" }}>
        Derivados automaticamente dos equipamentos dos funcionários alocados.
      </p>
      <DataTable
        colunas={colEquip}
        itens={obra.equipamentos_derivados}
        vazio="Nenhum equipamento (os funcionários alocados não têm equipamentos)."
      />
    </section>
  );
}

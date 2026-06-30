// Detalhe de uma obra: dados + gestão das alocações de funcionários e
// equipamentos (alocar/desalocar, cada um com o seu período).

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useCrud } from "../api/useCrud";
import { useOpcoes } from "../api/useOpcoes";
import { type Campo } from "../components/CrudForm";
import BotaoEditar from "../components/BotaoEditar";
import DataTable, { type Coluna } from "../components/DataTable";
import ModalForm from "../components/ModalForm";
import type {
  AlocacaoEquipamento,
  AlocacaoFuncionario,
  Equipamento,
  Funcionario,
  Obra,
} from "../api/types";

export default function ObraDetalhe() {
  const { id } = useParams<{ id: string }>();
  const obraId = Number(id);

  const [obra, setObra] = useState<Obra | null>(null);

  useEffect(() => {
    api.get<Obra>(`/obras/${obraId}/`).then((res) => setObra(res.data));
  }, [obraId]);

  // Alocações filtradas por esta obra; recarregam quando se aloca/desaloca.
  const aFunc = useCrud<AlocacaoFuncionario>(
    "/alocacoes-funcionarios/",
    `?obra=${obraId}`,
  );
  const aEquip = useCrud<AlocacaoEquipamento>(
    "/alocacoes-equipamentos/",
    `?obra=${obraId}`,
  );

  // Selects: só ativos (a API rejeita inativos, mas escondê-los melhora a UX).
  const funcionarios = useOpcoes<Funcionario>("/funcionarios/?ativo=true", (f) => f.nome);
  const equipamentos = useOpcoes<Equipamento>("/equipamentos/?ativo=true", (e) => e.nome);

  if (!obra) return <p className="muted">A carregar…</p>;

  // A data de fim de uma alocação não pode ultrapassar o fim previsto da obra
  // (se a obra tiver um). undefined = sem limite no input.
  const maxFim = obra.data_fim_prevista ?? undefined;

  const camposFunc: Campo[] = [
    { nome: "funcionario", etiqueta: "Funcionário", obrigatorio: true, opcoes: funcionarios },
    { nome: "data_inicio", etiqueta: "Início", tipo: "date", obrigatorio: true },
    { nome: "data_fim", etiqueta: "Fim (opcional)", tipo: "date", max: maxFim },
  ];
  const camposEquip: Campo[] = [
    { nome: "equipamento", etiqueta: "Equipamento", obrigatorio: true, opcoes: equipamentos },
    { nome: "data_inicio", etiqueta: "Início", tipo: "date", obrigatorio: true },
    { nome: "data_fim", etiqueta: "Fim (opcional)", tipo: "date", max: maxFim },
  ];

  const colFunc: Coluna<AlocacaoFuncionario>[] = [
    { cabecalho: "Funcionário", render: (a) => a.funcionario_nome },
    { cabecalho: "Início", render: (a) => a.data_inicio },
    { cabecalho: "Fim", render: (a) => a.data_fim ?? "—" },
  ];
  const colEquip: Coluna<AlocacaoEquipamento>[] = [
    { cabecalho: "Equipamento", render: (a) => a.equipamento_nome },
    { cabecalho: "Início", render: (a) => a.data_inicio },
    { cabecalho: "Fim", render: (a) => a.data_fim ?? "—" },
  ];

  // Na edição de uma alocação só se mexem as datas (não se troca o recurso).
  const camposEditarDatas: Campo[] = [
    { nome: "data_inicio", etiqueta: "Início", tipo: "date", obrigatorio: true },
    { nome: "data_fim", etiqueta: "Fim (opcional)", tipo: "date", max: maxFim },
  ];

  // Ao criar uma alocação, injeta sempre o id desta obra.
  const criarFunc = (dados: Record<string, unknown>) =>
    aFunc.criar({ ...dados, obra: obraId });
  const criarEquip = (dados: Record<string, unknown>) =>
    aEquip.criar({ ...dados, obra: obraId });

  async function desalocar(recurso: typeof aFunc | typeof aEquip, id: number) {
    if (!confirm("Remover esta alocação?")) return;
    await recurso.apagar(id);
  }

  return (
    <section>
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
          <BotaoEditar item={a} titulo="Editar alocação" campos={camposEditarDatas} onEditar={aFunc.editar} />
        )}
        onApagar={(a) => desalocar(aFunc, a.id)}
        vazio="Nenhum funcionário alocado."
      />

      <div className="acoes-header" style={{ marginTop: "2rem" }}>
        <h2>Equipamentos alocados</h2>
        <ModalForm textoBotao="+ Alocar equipamento" titulo="Alocar equipamento" campos={camposEquip} onCriar={criarEquip} />
      </div>
      <DataTable
        colunas={colEquip}
        itens={aEquip.itens}
        acoes={(a) => (
          <BotaoEditar item={a} titulo="Editar alocação" campos={camposEditarDatas} onEditar={aEquip.editar} />
        )}
        onApagar={(a) => desalocar(aEquip, a.id)}
        vazio="Nenhum equipamento alocado."
      />
    </section>
  );
}

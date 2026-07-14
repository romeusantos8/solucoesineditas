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

  if (!obra) return <p className="muted">A carregar…</p>;

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

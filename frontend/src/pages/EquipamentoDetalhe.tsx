// Detalhe de um equipamento: certificados associados.

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { useCrud } from "../api/useCrud";
import { type Campo } from "../components/CrudForm";
import BotaoEditar from "../components/BotaoEditar";
import DataTable, { type Coluna } from "../components/DataTable";
import ModalForm from "../components/ModalForm";
import type { Certificado, Equipamento } from "../api/types";

export default function EquipamentoDetalhe() {
  const { id } = useParams<{ id: string }>();
  const equipId = Number(id);
  const [equip, setEquip] = useState<Equipamento | null>(null);

  useEffect(() => {
    api.get<Equipamento>(`/equipamentos/${equipId}/`).then((res) => setEquip(res.data));
  }, [equipId]);

  const certificados = useCrud<Certificado>("/certificados/", `?equipamento=${equipId}`);

  if (!equip) return <p className="muted">A carregar…</p>;

  const campos: Campo[] = [
    { nome: "tipo", etiqueta: "Tipo de certificação", obrigatorio: true },
    { nome: "data_emissao", etiqueta: "Emissão", tipo: "date", obrigatorio: true },
    { nome: "data_validade", etiqueta: "Validade", tipo: "date", obrigatorio: true },
  ];
  const colunas: Coluna<Certificado>[] = [
    { cabecalho: "Tipo", render: (c) => c.tipo },
    { cabecalho: "Emissão", render: (c) => c.data_emissao },
    { cabecalho: "Validade", render: (c) => c.data_validade },
    { cabecalho: "Dias", render: (c) => c.dias_para_expirar },
  ];

  const criar = (dados: Record<string, unknown>) =>
    certificados.criar({ ...dados, equipamento: equipId });

  return (
    <section>
      <h1>{equip.nome}</h1>
      {equip.numero_serie && <p className="muted">Nº de série: {equip.numero_serie}</p>}

      <div className="acoes-header">
        <h2>Certificados</h2>
        <ModalForm textoBotao="+ Novo certificado" titulo="Novo certificado" campos={campos} onCriar={criar} />
      </div>
      <DataTable
        colunas={colunas}
        itens={certificados.itens}
        acoes={(c) => <BotaoEditar item={c} titulo="Editar certificado" campos={campos} onEditar={certificados.editar} />}
        onApagar={(c) => certificados.apagar(c.id)}
        vazio="Sem certificados."
      />
    </section>
  );
}

// Página CRUD completa: cabeçalho com botão "+ Novo" (abre modal) + tabela.
//
// Junta useCrud + ModalForm + DataTable. Uma página de listagem fica reduzida a
// declarar o recurso, os campos do formulário e as colunas da tabela.

import type { ReactNode } from "react";
import { useCrud } from "../api/useCrud";
import BotaoEditar from "./BotaoEditar";
import DataTable, { type Coluna } from "./DataTable";
import Dica from "./Dica";
import ModalForm from "./ModalForm";
import type { Campo } from "./CrudForm";

interface CrudPageProps<T extends { id: number }> {
  titulo: string;
  recurso: string; // ex.: "/viaturas/"
  tituloForm: string;
  textoBotao?: string;
  campos: Campo[];
  colunas: Coluna<T>[];
  // Aviso mostrado quando o apagar falha (normalmente por PROTECT no backend).
  avisoApagar?: string;
  vazio?: string;
  // Dica opcional mostrada acima da tabela (ex.: "clica no nome para detalhes").
  dica?: ReactNode;
}

export default function CrudPage<T extends { id: number }>({
  titulo,
  recurso,
  tituloForm,
  textoBotao,
  campos,
  colunas,
  avisoApagar = "Não foi possível apagar (pode ter registos associados).",
  vazio,
  dica,
}: CrudPageProps<T>) {
  const { itens, aCarregar, erro, criar, editar, apagar } = useCrud<T>(recurso);

  async function confirmarApagar(item: T) {
    if (!confirm("Apagar este registo?")) return;
    try {
      await apagar(item.id);
    } catch {
      alert(avisoApagar);
    }
  }

  return (
    <section>
      <div className="acoes-header">
        <h1>{titulo}</h1>
        <ModalForm
          textoBotao={textoBotao ?? `+ ${tituloForm}`}
          titulo={tituloForm}
          campos={campos}
          onCriar={criar}
        />
      </div>
      {erro && <div className="alert-erro">{erro}</div>}
      {dica && <Dica>{dica}</Dica>}
      {aCarregar ? (
        <p className="muted">A carregar…</p>
      ) : (
        <DataTable
          colunas={colunas}
          itens={itens}
          acoes={(item) => (
            <BotaoEditar
              item={item}
              titulo={`Editar — ${tituloForm}`}
              campos={campos}
              onEditar={editar}
            />
          )}
          onApagar={confirmarApagar}
          vazio={vazio}
        />
      )}
    </section>
  );
}

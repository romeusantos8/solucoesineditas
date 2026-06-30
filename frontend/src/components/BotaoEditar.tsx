// Botão "Editar" que abre um modal pré-preenchido com os valores do item e faz
// PATCH ao guardar. Reutiliza o CrudForm em modo edição.

import { useState } from "react";
import Modal from "./Modal";
import CrudForm, { type Campo } from "./CrudForm";

interface BotaoEditarProps<T extends { id: number }> {
  item: T;
  titulo: string;
  campos: Campo[];
  onEditar: (id: number, dados: Record<string, unknown>) => Promise<void>;
}

// Converte o valor de um campo do item numa string para o input. null/undefined
// → "" (campo vazio); tudo o resto → String(valor). FKs já vêm como id numérico.
function valorInicial(item: Record<string, unknown>, campo: Campo): string {
  const v = item[campo.nome];
  if (v === null || v === undefined) return "";
  return String(v);
}

export default function BotaoEditar<T extends { id: number }>({
  item,
  titulo,
  campos,
  onEditar,
}: BotaoEditarProps<T>) {
  const [aberto, setAberto] = useState(false);

  const iniciais: Record<string, string> = {};
  for (const campo of campos) {
    iniciais[campo.nome] = valorInicial(item as Record<string, unknown>, campo);
  }

  return (
    <>
      <button className="btn-link" onClick={() => setAberto(true)}>
        Editar
      </button>
      <Modal aberto={aberto} titulo={titulo} onFechar={() => setAberto(false)}>
        <CrudForm
          campos={campos}
          valoresIniciais={iniciais}
          onSubmeter={(dados) => onEditar(item.id, dados)}
          onSucesso={() => setAberto(false)}
        />
      </Modal>
    </>
  );
}

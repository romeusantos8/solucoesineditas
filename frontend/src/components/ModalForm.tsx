// Botão que abre um modal com um formulário de criação dentro.
//
// Junta o padrão repetido: um botão "+ Novo…", o Modal, e o CrudForm. Ao criar
// com sucesso, fecha o modal. É o que as páginas usam para adicionar registos.

import { useState } from "react";
import Modal from "./Modal";
import CrudForm, { type Campo } from "./CrudForm";

interface ModalFormProps {
  // Texto do botão que abre o modal (ex.: "+ Nova viatura").
  textoBotao: string;
  // Título do modal (ex.: "Nova viatura").
  titulo: string;
  campos: Campo[];
  onCriar: (dados: Record<string, unknown>) => Promise<void>;
}

export default function ModalForm({
  textoBotao,
  titulo,
  campos,
  onCriar,
}: ModalFormProps) {
  const [aberto, setAberto] = useState(false);

  return (
    <>
      <button onClick={() => setAberto(true)}>{textoBotao}</button>
      <Modal aberto={aberto} titulo={titulo} onFechar={() => setAberto(false)}>
        <CrudForm
          campos={campos}
          onSubmeter={onCriar}
          onSucesso={() => setAberto(false)}
        />
      </Modal>
    </>
  );
}

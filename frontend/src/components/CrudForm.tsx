// Formulário genérico de criação/edição a partir de uma definição de campos.
//
// Pensado para viver dentro de um Modal: gere o estado dos inputs, submete
// (chamando `onSubmeter`), mostra erros de validação da API e, em sucesso, limpa
// e chama `onSucesso` (normalmente para fechar o modal e recarregar a lista).
//
// `valoresIniciais` pré-preenche os campos (modo edição). Os valores são
// enviados como strings; o backend faz a coerção.

import { useState, type FormEvent } from "react";
import { primeiraMensagemErro } from "../api/useCrud";

export interface Campo {
  nome: string;
  etiqueta: string;
  tipo?: "text" | "number" | "date" | "email";
  obrigatorio?: boolean;
  // Para campos de escolha (select). Se presente, rende um <select>.
  opcoes?: { valor: string | number; texto: string }[];
  // Campo de texto que é unique+nullable no backend (ex.: NIF, nº de série):
  // vazio tem de ir como null (não ""), senão dois vazios colidem no unique.
  vazioComoNull?: boolean;
  // Limite superior para campos de data (atributo HTML max="YYYY-MM-DD").
  max?: string;
}

interface CrudFormProps {
  campos: Campo[];
  onSubmeter: (dados: Record<string, unknown>) => Promise<void>;
  onSucesso?: () => void;
  textoBotao?: string;
  // Valores a pré-preencher (modo edição). Chaves = nomes dos campos.
  valoresIniciais?: Record<string, string>;
}

export default function CrudForm({
  campos,
  onSubmeter,
  onSucesso,
  textoBotao = "Guardar",
  valoresIniciais = {},
}: CrudFormProps) {
  const [valores, setValores] = useState<Record<string, string>>(valoresIniciais);
  const [erro, setErro] = useState<string | null>(null);
  const [aGuardar, setAGuardar] = useState(false);

  function definir(nome: string, valor: string) {
    setValores((v) => ({ ...v, [nome]: valor }));
  }

  async function submeter(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setAGuardar(true);
    // Como tratar um campo opcional deixado vazio depende do tipo:
    //  - texto/email → "" (no backend são CharField/EmailField com blank=True,
    //    que aceitam vazio mas NÃO null);
    //  - número/data/select(FK) → null (não há "string vazia" válida para eles).
    const dados: Record<string, unknown> = {};
    for (const campo of campos) {
      const v = valores[campo.nome] ?? "";
      if (v !== "") {
        dados[campo.nome] = v;
      } else if (campo.vazioComoNull) {
        dados[campo.nome] = null; // texto unique+nullable (ex.: NIF)
      } else {
        const ehTexto =
          !campo.opcoes && (campo.tipo === undefined || campo.tipo === "text" || campo.tipo === "email");
        dados[campo.nome] = ehTexto ? "" : null;
      }
    }
    try {
      await onSubmeter(dados);
      onSucesso?.();
    } catch (err) {
      setErro(primeiraMensagemErro(err));
    } finally {
      setAGuardar(false);
    }
  }

  return (
    <form className="form-modal" onSubmit={submeter}>
      {erro && <div className="alert-erro">{erro}</div>}
      {campos.map((campo) => (
        <label key={campo.nome}>
          {campo.etiqueta}
          <FieldInput
            campo={campo}
            valor={valores[campo.nome] ?? ""}
            onChange={(v) => definir(campo.nome, v)}
          />
        </label>
      ))}
      <button type="submit" disabled={aGuardar}>
        {aGuardar ? "A guardar…" : textoBotao}
      </button>
    </form>
  );
}

function FieldInput({
  campo,
  valor,
  onChange,
}: {
  campo: Campo;
  valor: string;
  onChange: (v: string) => void;
}) {
  if (campo.opcoes) {
    return (
      <select
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        required={campo.obrigatorio}
      >
        <option value="">Selecionar…</option>
        {campo.opcoes.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.texto}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      type={campo.tipo ?? "text"}
      value={valor}
      onChange={(e) => onChange(e.target.value)}
      required={campo.obrigatorio}
      max={campo.tipo === "date" ? campo.max : undefined}
    />
  );
}

// Tabela genérica a partir de uma definição declarativa de colunas.
//
// Cada coluna diz o cabeçalho e como obter o valor de cada linha (uma função).
// Opcionalmente, uma coluna pode ter `className` por linha (ex.: cores por
// urgência). A prop `acoes` renderiza botões por linha (ex.: Editar + Apagar) na
// última coluna; `onApagar` é um atalho que adiciona só o botão Apagar.

import type { ReactNode } from "react";

export interface Coluna<T> {
  cabecalho: string;
  // Como renderizar a célula desta coluna para a linha `item`.
  render: (item: T) => ReactNode;
}

interface DataTableProps<T extends { id: number }> {
  colunas: Coluna<T>[];
  itens: T[];
  // Classe CSS por linha (ex.: realce de urgência). Opcional.
  classeLinha?: (item: T) => string | undefined;
  // Botões de ação por linha (ex.: <BotaoEditar/> + Apagar). Opcional.
  acoes?: (item: T) => ReactNode;
  // Atalho: mostra só um botão "Apagar" por linha.
  onApagar?: (item: T) => void;
  vazio?: string;
}

export default function DataTable<T extends { id: number }>({
  colunas,
  itens,
  classeLinha,
  acoes,
  onApagar,
  vazio = "Sem registos.",
}: DataTableProps<T>) {
  if (itens.length === 0) {
    return <div className="card">{vazio}</div>;
  }

  const temAcoes = Boolean(acoes || onApagar);

  return (
    <table className="tabela">
      <thead>
        <tr>
          {colunas.map((c) => (
            <th key={c.cabecalho}>{c.cabecalho}</th>
          ))}
          {temAcoes && <th></th>}
        </tr>
      </thead>
      <tbody>
        {itens.map((item) => (
          <tr key={item.id} className={classeLinha?.(item)}>
            {colunas.map((c) => (
              <td key={c.cabecalho}>{c.render(item)}</td>
            ))}
            {temAcoes && (
              <td className="celula-acoes">
                {acoes?.(item)}
                {onApagar && (
                  <button className="btn-link danger" onClick={() => onApagar(item)}>
                    Apagar
                  </button>
                )}
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

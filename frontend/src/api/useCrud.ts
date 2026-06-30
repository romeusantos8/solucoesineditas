// Hook genérico de CRUD sobre um endpoint paginado do DRF.
//
// Encapsula o que todas as páginas de listagem repetiam: carregar a lista
// (paginada), criar, apagar, e gerir estados de loading/erro. Recebe o caminho
// do recurso (ex.: "/viaturas/") e o tipo dos itens.
//
// Uso:
//   const { itens, aCarregar, erro, criar, apagar, recarregar } =
//     useCrud<Viatura>("/viaturas/");

import { useCallback, useEffect, useState } from "react";
import { AxiosError } from "axios";
import { api } from "./client";
import type { Paginated } from "./types";

// Extrai a primeira mensagem de erro de validação (400) do DRF, para mostrar ao
// utilizador. Funciona com {campo: ["msg"]} e {campo: "msg"}.
export function primeiraMensagemErro(err: unknown): string {
  if (err instanceof AxiosError && err.response?.status === 400) {
    const dados = err.response.data as Record<string, string[] | string>;
    const primeiro = Object.values(dados)[0];
    return Array.isArray(primeiro) ? primeiro[0] : String(primeiro);
  }
  return "Ocorreu um erro. Tenta novamente.";
}

interface UseCrud<T> {
  itens: T[];
  total: number;
  aCarregar: boolean;
  erro: string | null;
  recarregar: () => void;
  criar: (dados: Record<string, unknown>) => Promise<void>;
  editar: (id: number, dados: Record<string, unknown>) => Promise<void>;
  apagar: (id: number) => Promise<void>;
}

export function useCrud<T extends { id: number }>(
  recurso: string,
  // querystring opcional (ex.: "?obra=3") para filtrar a lista.
  query = "",
): UseCrud<T> {
  const [itens, setItens] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const recarregar = useCallback(() => {
    setACarregar(true);
    setErro(null);
    api
      .get<Paginated<T>>(`${recurso}${query}`)
      .then((res) => {
        setItens(res.data.results);
        setTotal(res.data.count);
      })
      .catch(() => setErro("Não foi possível carregar os dados."))
      .finally(() => setACarregar(false));
  }, [recurso, query]);

  useEffect(recarregar, [recarregar]);

  async function criar(dados: Record<string, unknown>) {
    // Deixa o erro propagar para o formulário tratar a mensagem por campo.
    await api.post(recurso, dados);
    recarregar();
  }

  async function editar(id: number, dados: Record<string, unknown>) {
    // PATCH: atualização parcial (só os campos enviados).
    await api.patch(`${recurso}${id}/`, dados);
    recarregar();
  }

  async function apagar(id: number) {
    await api.delete(`${recurso}${id}/`);
    recarregar();
  }

  return { itens, total, aCarregar, erro, recarregar, criar, editar, apagar };
}

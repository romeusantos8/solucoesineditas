// Carrega uma lista de um recurso e converte cada item numa opção {valor,texto}
// para usar em <select> (campos de escolha do CrudForm).
//
//   const opcoesClientes = useOpcoes<Cliente>("/clientes/", (c) => c.nome);

import { useEffect, useState } from "react";
import { api } from "./client";
import type { Paginated } from "./types";

export function useOpcoes<T extends { id: number }>(
  recurso: string,
  texto: (item: T) => string,
) {
  const [opcoes, setOpcoes] = useState<{ valor: number; texto: string }[]>([]);

  useEffect(() => {
    let ativo = true;
    api.get<Paginated<T>>(recurso).then((res) => {
      if (ativo) {
        setOpcoes(res.data.results.map((i) => ({ valor: i.id, texto: texto(i) })));
      }
    });
    return () => {
      ativo = false;
    };
    // texto é estável (definido fora do render); só recarrega se o recurso mudar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recurso]);

  return opcoes;
}

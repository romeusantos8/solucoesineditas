// Tipos TypeScript que espelham as respostas da API Django.
// Mantê-los a par dos serializers evita surpresas em runtime.

// O DRF devolve listas paginadas com esta forma.
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Viatura {
  id: number;
  matricula: string;
  marca: string;
  modelo: string;
  ano: number | null;
  ativa: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface Equipamento {
  id: number;
  nome: string;
  numero_serie: string | null;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
}

// Item do dashboard de alertas (/api/alerts/). Forma unificada das 3 fontes.
export interface Alerta {
  tipo: "seguro" | "inspecao" | "certificado";
  descricao: string;
  data_validade: string;
  dias_para_expirar: number;
  expirado: boolean;
  recurso: "viatura" | "equipamento";
  recurso_id: number;
  registo_id: number;
}

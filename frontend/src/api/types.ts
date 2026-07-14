// Tipos TypeScript que espelham as respostas da API Django.
// Mantê-los a par dos serializers evita surpresas em runtime.

// O DRF devolve listas paginadas com esta forma.
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Campos de auditoria comuns a quase todas as entidades (read-only).
export interface Auditoria {
  criado_por: number | null;
  atualizado_por: number | null;
}

// --- Frota ---
export interface Viatura extends Auditoria {
  id: number;
  matricula: string;
  marca: string;
  modelo: string;
  ano: number | null;
  ativa: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface SeguroViatura extends Auditoria {
  id: number;
  viatura: number;
  seguradora: string;
  apolice: string;
  data_inicio: string;
  data_validade: string;
  dias_para_expirar: number;
}

export interface Inspecao extends Auditoria {
  id: number;
  viatura: number;
  data_inspecao: string;
  data_validade: string;
  resultado: "aprovado" | "reprovado";
  dias_para_expirar: number;
}

export interface DespesaViatura extends Auditoria {
  id: number;
  viatura: number;
  descricao: string;
  valor: string;
  data: string;
}

// --- Equipamentos ---
export interface Equipamento extends Auditoria {
  id: number;
  nome: string;
  numero_serie: string | null;
  ativo: boolean;
  responsavel: number | null;
  responsavel_nome: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface Certificado extends Auditoria {
  id: number;
  equipamento: number;
  tipo: string;
  data_emissao: string;
  data_validade: string;
  dias_para_expirar: number;
}

// --- Funcionários ---
export interface Funcionario extends Auditoria {
  id: number;
  nome: string;
  nif: string | null;
  funcao: string;
  data_admissao: string;
  ativo: boolean;
  email: string;
  telefone: string;
  criado_em: string;
  atualizado_em: string;
}

export interface DespesaFuncionario extends Auditoria {
  id: number;
  funcionario: number;
  descricao: string;
  valor: string;
  data: string;
}

// --- Clientes e Obras ---
export interface Cliente extends Auditoria {
  id: number;
  nome: string;
  nif: string | null;
  email: string;
  telefone: string;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
}

export type EstadoObra = "planeada" | "em_curso" | "concluida" | "cancelada";

export interface AlocacaoFuncionario extends Auditoria {
  id: number;
  obra: number;
  funcionario: number;
  funcionario_nome: string;
  data_inicio: string;
  data_fim: string | null;
}

// Equipamento derivado numa obra (vem do funcionário responsável, só leitura).
export interface EquipamentoDerivado {
  id: number;
  nome: string;
  numero_serie: string | null;
  funcionario_id: number;
  funcionario_nome: string;
}

export interface Obra extends Auditoria {
  id: number;
  cliente: number;
  nome: string;
  descricao: string;
  data_inicio: string;
  data_fim_prevista: string | null;
  estado: EstadoObra;
  alocacoes_funcionarios: AlocacaoFuncionario[];
  equipamentos_derivados: EquipamentoDerivado[];
  criado_em: string;
  atualizado_em: string;
}

// --- Ficha médica (dados de saúde, acesso restrito a staff) ---
export type Aptidao = "apto" | "apto_restricoes" | "nao_apto";

export interface FichaMedica extends Auditoria {
  id: number;
  funcionario: number;
  aptidao: Aptidao;
  data_exame: string;
  data_validade: string;
  dias_para_expirar: number;
  medico: string;
  observacoes: string;
  criado_em: string;
  atualizado_em: string;
}

// --- Relatórios ---
export interface TotalMensal {
  mes: number; // 1-12
  total: string;
}
export interface DespesaDetalhe {
  id: number;
  descricao: string;
  valor: string;
  data: string;
}
export interface RelatorioDespesas {
  tipo: "funcionario" | "viatura";
  entidade: number;
  ano: number;
  total_ano: string;
  meses: TotalMensal[];
  mes?: number;
  detalhe?: DespesaDetalhe[];
}

// Item do dashboard de alertas (/api/alerts/). Forma unificada das fontes.
export interface Alerta {
  tipo: "seguro" | "inspecao" | "certificado" | "ficha_medica";
  descricao: string;
  data_validade: string;
  dias_para_expirar: number;
  expirado: boolean;
  recurso: "viatura" | "equipamento" | "funcionario";
  recurso_id: number;
  registo_id: number;
}

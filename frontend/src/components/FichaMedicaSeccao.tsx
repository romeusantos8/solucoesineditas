// Secção da ficha médica de um funcionário (dados de saúde, acesso restrito).
//
// Carrega a ficha (filtrada pelo funcionário). Comportamento:
// - 403 → o utilizador não é staff: esconde a secção por completo.
// - sem ficha → mostra botão para criar (modal).
// - com ficha → mostra os dados; permite substituir (apaga + cria) implícito
//   via criação não é trivial com OneToOne, por isso aqui só listamos e
//   permitimos remover; recriar é criar de novo depois de remover.

import { useCallback, useEffect, useState } from "react";
import { AxiosError } from "axios";
import { api } from "../api/client";
import type { FichaMedica, Paginated } from "../api/types";
import ModalForm from "./ModalForm";
import type { Campo } from "./CrudForm";

const APTIDAO_LABEL: Record<FichaMedica["aptidao"], string> = {
  apto: "Apto",
  apto_restricoes: "Apto com restrições",
  nao_apto: "Não apto",
};

const campos: Campo[] = [
  {
    nome: "aptidao",
    etiqueta: "Aptidão",
    obrigatorio: true,
    opcoes: [
      { valor: "apto", texto: "Apto" },
      { valor: "apto_restricoes", texto: "Apto com restrições" },
      { valor: "nao_apto", texto: "Não apto" },
    ],
  },
  { nome: "data_exame", etiqueta: "Data do exame", tipo: "date", obrigatorio: true },
  { nome: "data_validade", etiqueta: "Validade", tipo: "date", obrigatorio: true },
  { nome: "medico", etiqueta: "Médico / entidade (opcional)" },
  { nome: "observacoes", etiqueta: "Observações (opcional)" },
];

export default function FichaMedicaSeccao({ funcionarioId }: { funcionarioId: number }) {
  const [ficha, setFicha] = useState<FichaMedica | null>(null);
  const [semAcesso, setSemAcesso] = useState(false);
  const [aCarregar, setACarregar] = useState(true);

  const carregar = useCallback(() => {
    setACarregar(true);
    api
      .get<Paginated<FichaMedica>>(`/fichas-medicas/?funcionario=${funcionarioId}`)
      .then((res) => setFicha(res.data.results[0] ?? null))
      .catch((err: AxiosError) => {
        // 403 = utilizador sem permissão para dados de saúde. Esconde a secção.
        if (err.response?.status === 403) setSemAcesso(true);
      })
      .finally(() => setACarregar(false));
  }, [funcionarioId]);

  useEffect(carregar, [carregar]);

  // Utilizador sem acesso: não mostra nada (nem sequer revela que existe ficha).
  if (semAcesso) return null;
  if (aCarregar) return null;

  async function criar(dados: Record<string, unknown>) {
    await api.post("/fichas-medicas/", { ...dados, funcionario: funcionarioId });
    carregar();
  }

  async function remover() {
    if (!ficha) return;
    if (!confirm("Remover a ficha médica?")) return;
    await api.delete(`/fichas-medicas/${ficha.id}/`);
    setFicha(null);
  }

  return (
    <>
      <div className="acoes-header" style={{ marginTop: "2rem" }}>
        <h2>Ficha médica</h2>
        {!ficha && (
          <ModalForm
            textoBotao="+ Criar ficha médica"
            titulo="Nova ficha médica"
            campos={campos}
            onCriar={criar}
          />
        )}
      </div>

      {ficha ? (
        <div className="card">
          <p><strong>Aptidão:</strong> {APTIDAO_LABEL[ficha.aptidao]}</p>
          <p><strong>Exame:</strong> {ficha.data_exame}</p>
          <p>
            <strong>Validade:</strong> {ficha.data_validade}{" "}
            <span className="muted">({ficha.dias_para_expirar} dias)</span>
          </p>
          {ficha.medico && <p><strong>Médico:</strong> {ficha.medico}</p>}
          {ficha.observacoes && <p><strong>Observações:</strong> {ficha.observacoes}</p>}
          <button className="btn-link danger" onClick={remover}>
            Remover ficha
          </button>
        </div>
      ) : (
        <div className="card">Sem ficha médica registada.</div>
      )}
    </>
  );
}

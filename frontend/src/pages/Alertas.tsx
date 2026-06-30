// Dashboard de prazos a expirar. Consome GET /api/alerts/?dias=N.

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Alerta, Paginated } from "../api/types";

const LABEL_TIPO: Record<Alerta["tipo"], string> = {
  seguro: "Seguro",
  inspecao: "Inspeção",
  certificado: "Certificado",
};

// Classe CSS conforme a urgência, para colorir cada linha.
function urgenciaClasse(a: Alerta): string {
  if (a.expirado) return "row-expirado";
  if (a.dias_para_expirar <= 30) return "row-urgente";
  return "row-proximo";
}

function textoPrazo(a: Alerta): string {
  if (a.expirado) return `Expirado há ${Math.abs(a.dias_para_expirar)} dias`;
  if (a.dias_para_expirar === 0) return "Expira hoje";
  return `Faltam ${a.dias_para_expirar} dias`;
}

export default function Alertas() {
  const [dias, setDias] = useState(60);
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [pagina, setPagina] = useState(1);
  const [total, setTotal] = useState(0);
  const [temProxima, setTemProxima] = useState(false);

  // Mudar a janela volta à primeira página (senão podíamos cair fora do range).
  useEffect(() => setPagina(1), [dias]);

  useEffect(() => {
    let ativo = true;
    setACarregar(true);
    setErro(null);
    api
      .get<Paginated<Alerta>>(`/alerts/?dias=${dias}&page=${pagina}`)
      .then((res) => {
        if (!ativo) return;
        setAlertas(res.data.results);
        setTotal(res.data.count);
        setTemProxima(res.data.next !== null);
      })
      .catch(() => {
        if (ativo) setErro("Não foi possível carregar os alertas.");
      })
      .finally(() => {
        if (ativo) setACarregar(false);
      });
    return () => {
      ativo = false;
    };
  }, [dias, pagina]);

  return (
    <section>
      <div className="page-header">
        <h1>Alertas de prazos</h1>
        <label className="filtro">
          Janela:
          <select value={dias} onChange={(e) => setDias(Number(e.target.value))}>
            <option value={30}>30 dias</option>
            <option value={60}>60 dias</option>
            <option value={90}>90 dias</option>
          </select>
        </label>
      </div>

      {erro && <div className="alert-erro">{erro}</div>}
      {aCarregar && <p className="muted">A carregar…</p>}

      {!aCarregar && !erro && alertas.length === 0 && (
        <div className="card">Sem prazos a expirar nesta janela. 🎉</div>
      )}

      {!aCarregar && alertas.length > 0 && (
        <table className="tabela">
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Descrição</th>
              <th>Validade</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {alertas.map((a) => (
              <tr
                key={`${a.tipo}-${a.registo_id}`}
                className={urgenciaClasse(a)}
              >
                <td>{LABEL_TIPO[a.tipo]}</td>
                <td>{a.descricao}</td>
                <td>{a.data_validade}</td>
                <td>{textoPrazo(a)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!aCarregar && total > 0 && (pagina > 1 || temProxima) && (
        <div className="paginacao">
          <button
            onClick={() => setPagina((p) => p - 1)}
            disabled={pagina <= 1}
          >
            Anterior
          </button>
          <span className="muted">
            Página {pagina} — {total} no total
          </span>
          <button onClick={() => setPagina((p) => p + 1)} disabled={!temProxima}>
            Seguinte
          </button>
        </div>
      )}
    </section>
  );
}

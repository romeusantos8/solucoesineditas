// Dashboard de prazos a expirar. Consome GET /api/alerts/?dias=N.
// Redesenho: KPIs de resumo, badges de severidade, ícones por tipo, pesquisa,
// ordenação e empty state. A lógica de fetch/paginação mantém-se.

import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { Alerta, Paginated } from "../api/types";
import {
  IconeCertificado,
  IconeFichaMedica,
  IconeInspecao,
  IconeOk,
  IconeSeguro,
  IconeLupa,
} from "../components/Icones";

const LABEL_TIPO: Record<Alerta["tipo"], string> = {
  seguro: "Seguro",
  inspecao: "Inspeção",
  certificado: "Certificado",
  ficha_medica: "Ficha médica",
};

function IconeTipo({ tipo }: { tipo: Alerta["tipo"] }) {
  if (tipo === "seguro") return <IconeSeguro />;
  if (tipo === "inspecao") return <IconeInspecao />;
  if (tipo === "certificado") return <IconeCertificado />;
  return <IconeFichaMedica />;
}

type Severidade = "critico" | "aviso" | "info";

// Crítico: já expirado ou ≤ 7 dias. Aviso: ≤ 30 dias. Info: o resto.
function severidade(a: Alerta): Severidade {
  if (a.expirado || a.dias_para_expirar <= 7) return "critico";
  if (a.dias_para_expirar <= 30) return "aviso";
  return "info";
}

function textoPrazo(a: Alerta): string {
  if (a.expirado) return `Expirado há ${Math.abs(a.dias_para_expirar)} dias`;
  if (a.dias_para_expirar === 0) return "Expira hoje";
  return `Faltam ${a.dias_para_expirar} dias`;
}

type Coluna = "tipo" | "descricao" | "data_validade" | "dias";

export default function Alertas() {
  const [dias, setDias] = useState(60);
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [pagina, setPagina] = useState(1);
  const [total, setTotal] = useState(0);
  const [temProxima, setTemProxima] = useState(false);

  const [pesquisa, setPesquisa] = useState("");
  const [ordenarPor, setOrdenarPor] = useState<Coluna>("dias");
  const [ascendente, setAscendente] = useState(true);

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

  // KPIs calculados sobre os alertas carregados (a janela já limita o volume).
  const kpis = useMemo(() => {
    let criticos = 0;
    let avisos = 0;
    for (const a of alertas) {
      const s = severidade(a);
      if (s === "critico") criticos++;
      else if (s === "aviso") avisos++;
    }
    return { total: alertas.length, criticos, avisos };
  }, [alertas]);

  // Pesquisa + ordenação (no cliente, sobre a página atual).
  const visiveis = useMemo(() => {
    const termo = pesquisa.trim().toLowerCase();
    let lista = alertas;
    if (termo) {
      lista = lista.filter(
        (a) =>
          a.descricao.toLowerCase().includes(termo) ||
          LABEL_TIPO[a.tipo].toLowerCase().includes(termo),
      );
    }
    const fator = ascendente ? 1 : -1;
    return [...lista].sort((a, b) => {
      switch (ordenarPor) {
        case "tipo":
          return LABEL_TIPO[a.tipo].localeCompare(LABEL_TIPO[b.tipo]) * fator;
        case "descricao":
          return a.descricao.localeCompare(b.descricao) * fator;
        case "data_validade":
          return a.data_validade.localeCompare(b.data_validade) * fator;
        default:
          return (a.dias_para_expirar - b.dias_para_expirar) * fator;
      }
    });
  }, [alertas, pesquisa, ordenarPor, ascendente]);

  function ordenar(coluna: Coluna) {
    if (coluna === ordenarPor) setAscendente((v) => !v);
    else {
      setOrdenarPor(coluna);
      setAscendente(true);
    }
  }

  function seta(coluna: Coluna) {
    if (coluna !== ordenarPor) return null;
    return <span className="seta">{ascendente ? "▲" : "▼"}</span>;
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>Alertas de prazos</h1>
          <p className="subtitulo">
            Seguros, inspeções, certificados e fichas médicas a expirar.
          </p>
        </div>
        <label className="filtro">
          Janela
          <select value={dias} onChange={(e) => setDias(Number(e.target.value))}>
            <option value={30}>30 dias</option>
            <option value={60}>60 dias</option>
            <option value={90}>90 dias</option>
          </select>
        </label>
      </div>

      {/* KPIs */}
      <div className="kpi-grid">
        <div className="kpi">
          <span className="kpi-icone is-info">
            <IconeAlertasMini />
          </span>
          <div>
            <div className="kpi-valor">{total}</div>
            <div className="kpi-rotulo">Total nesta janela</div>
          </div>
        </div>
        <div className="kpi">
          <span className="kpi-icone is-critico">
            <IconeAlertasMini />
          </span>
          <div>
            <div className="kpi-valor">{kpis.criticos}</div>
            <div className="kpi-rotulo">Críticos (≤ 7 dias / vencidos)</div>
          </div>
        </div>
        <div className="kpi">
          <span className="kpi-icone is-aviso">
            <IconeRelogio />
          </span>
          <div>
            <div className="kpi-valor">{kpis.avisos}</div>
            <div className="kpi-rotulo">A vigiar (≤ 30 dias)</div>
          </div>
        </div>
      </div>

      {erro && <div className="alert-erro">{erro}</div>}

      {/* Toolbar: pesquisa */}
      {!aCarregar && total > 0 && (
        <div className="toolbar">
          <div className="campo-pesquisa">
            <span className="lupa">
              <IconeLupa />
            </span>
            <input
              type="search"
              placeholder="Pesquisar por descrição ou tipo…"
              value={pesquisa}
              onChange={(e) => setPesquisa(e.target.value)}
              aria-label="Pesquisar alertas"
            />
          </div>
        </div>
      )}

      {aCarregar && <p className="muted">A carregar…</p>}

      {/* Empty state */}
      {!aCarregar && !erro && total === 0 && (
        <div className="empty-state">
          <div className="empty-icone">
            <IconeOk />
          </div>
          <h3>Tudo em dia</h3>
          <p>Não há prazos a expirar nesta janela temporal.</p>
        </div>
      )}

      {/* Tabela */}
      {!aCarregar && total > 0 && (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th className="ordenavel" onClick={() => ordenar("tipo")}>
                  Tipo {seta("tipo")}
                </th>
                <th className="ordenavel" onClick={() => ordenar("descricao")}>
                  Descrição {seta("descricao")}
                </th>
                <th className="ordenavel" onClick={() => ordenar("data_validade")}>
                  Validade {seta("data_validade")}
                </th>
                <th className="ordenavel" onClick={() => ordenar("dias")}>
                  Estado {seta("dias")}
                </th>
              </tr>
            </thead>
            <tbody>
              {visiveis.map((a) => {
                const sev = severidade(a);
                return (
                  <tr key={`${a.tipo}-${a.registo_id}`} className={`sev-${sev}`}>
                    <td>
                      <span className="tipo-cell">
                        <span className="tipo-icone">
                          <IconeTipo tipo={a.tipo} />
                        </span>
                        {LABEL_TIPO[a.tipo]}
                      </span>
                    </td>
                    <td>{a.descricao}</td>
                    <td>{a.data_validade}</td>
                    <td>
                      <span className={`badge badge-${sev === "info" ? "info" : sev}`}>
                        <span className="ponto" />
                        {textoPrazo(a)}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {visiveis.length === 0 && (
                <tr>
                  <td colSpan={4} className="muted" style={{ textAlign: "center" }}>
                    Nenhum alerta corresponde à pesquisa.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Paginação */}
      {!aCarregar && total > 0 && (pagina > 1 || temProxima) && (
        <div className="paginacao">
          <span className="info">
            Página {pagina} — {total} no total
          </span>
          <button
            className="btn-secundario"
            onClick={() => setPagina((p) => p - 1)}
            disabled={pagina <= 1}
          >
            Anterior
          </button>
          <button
            className="btn-secundario"
            onClick={() => setPagina((p) => p + 1)}
            disabled={!temProxima}
          >
            Seguinte
          </button>
        </div>
      )}
    </section>
  );
}

// Ícone pequeno para o KPI "total" (sino/alerta simplificado).
function IconeAlertasMini() {
  return (
    <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" />
    </svg>
  );
}

// Relógio (KPI "a vigiar").
function IconeRelogio() {
  return (
    <svg width={20} height={20} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

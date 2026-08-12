// Aba de Relatórios: despesas por mês de um funcionário ou viatura, num ano.
// Mostra um gráfico de barras + tabela; clicar num mês abre o detalhe.

import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useOpcoes } from "../api/useOpcoes";
import Dica from "../components/Dica";
import type {
  Funcionario,
  Obra,
  RelatorioDespesas,
  RelatorioEquipamentosFuncionario,
  RelatorioFaturacaoObra,
  Viatura,
} from "../api/types";

const MESES = [
  "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
  "Jul", "Ago", "Set", "Out", "Nov", "Dez",
];

const anoAtual = new Date().getFullYear();
const ANOS = [anoAtual, anoAtual - 1, anoAtual - 2, anoAtual - 3];

function eur(valor: string | number): string {
  const n = typeof valor === "string" ? Number(valor) : valor;
  return n.toLocaleString("pt-PT", { style: "currency", currency: "EUR" });
}

export default function Relatorios() {
  const [tipo, setTipo] = useState<"funcionario" | "viatura">("funcionario");
  const [entidade, setEntidade] = useState<string>("");
  const [ano, setAno] = useState<number>(anoAtual);
  const [mesDetalhe, setMesDetalhe] = useState<number | null>(null);

  const [dados, setDados] = useState<RelatorioDespesas | null>(null);
  const [aCarregar, setACarregar] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const funcionarios = useOpcoes<Funcionario>("/funcionarios/", (f) => f.nome);
  const viaturas = useOpcoes<Viatura>("/viaturas/", (v) => `${v.matricula} (${v.marca})`);
  const opcoesEntidade = tipo === "funcionario" ? funcionarios : viaturas;

  // Ao trocar de tipo, limpa a entidade escolhida (ids não são compatíveis).
  useEffect(() => {
    setEntidade("");
    setDados(null);
    setMesDetalhe(null);
  }, [tipo]);

  // Carrega o relatório quando há entidade + ano (+ mês para detalhe).
  useEffect(() => {
    if (!entidade) {
      setDados(null);
      return;
    }
    setACarregar(true);
    setErro(null);
    const q = new URLSearchParams({ tipo, entidade, ano: String(ano) });
    if (mesDetalhe) q.set("mes", String(mesDetalhe));
    api
      .get<RelatorioDespesas>(`/reports/despesas-mensais/?${q.toString()}`)
      .then((res) => setDados(res.data))
      .catch(() => setErro("Não foi possível carregar o relatório."))
      .finally(() => setACarregar(false));
  }, [tipo, entidade, ano, mesDetalhe]);

  // Máximo para escalar as barras.
  const maxTotal = useMemo(() => {
    if (!dados) return 0;
    return Math.max(...dados.meses.map((m) => Number(m.total)), 0);
  }, [dados]);

  return (
    <section>
      <div className="page-header">
        <div>
          <h1>Relatórios</h1>
          <p className="subtitulo">Despesas por mês de funcionários e viaturas. Faturação por obra e equipamentos de funcionários.</p>
        </div>
      </div>

      {/* Filtros */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="form-row">
          <label>
            Tipo
            <select value={tipo} onChange={(e) => setTipo(e.target.value as "funcionario" | "viatura")}>
              <option value="funcionario">Funcionário</option>
              <option value="viatura">Viatura</option>
            </select>
          </label>
          <label>
            {tipo === "funcionario" ? "Funcionário" : "Viatura"}
            <select value={entidade} onChange={(e) => { setEntidade(e.target.value); setMesDetalhe(null); }}>
              <option value="">Selecionar…</option>
              {opcoesEntidade.map((o) => (
                <option key={o.valor} value={o.valor}>{o.texto}</option>
              ))}
            </select>
          </label>
          <label>
            Ano
            <select value={ano} onChange={(e) => { setAno(Number(e.target.value)); setMesDetalhe(null); }}>
              {ANOS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </label>
        </div>
      </div>

      {erro && <div className="alert-erro">{erro}</div>}
      {aCarregar && <p className="muted">A carregar…</p>}

      {!entidade && !aCarregar && (
        <div className="empty-state">
          <h3>Escolhe uma entidade</h3>
          <p>Seleciona um {tipo === "funcionario" ? "funcionário" : "viatura"} e um ano para ver as despesas.</p>
        </div>
      )}

      {dados && !aCarregar && (
        <>
          {/* Resumo do ano */}
          <div className="kpi-grid">
            <div className="kpi">
              <span className="kpi-icone is-info">€</span>
              <div>
                <div className="kpi-valor">{eur(dados.total_ano)}</div>
                <div className="kpi-rotulo">Total em {dados.ano}</div>
              </div>
            </div>
          </div>

          <Dica>
            Clica numa <strong>barra do gráfico</strong> (um mês) para ver o
            detalhe das despesas desse mês.
          </Dica>

          {/* Gráfico de barras */}
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ marginBottom: "1rem" }}>Despesas por mês</h2>
            <div className="grafico-barras">
              {dados.meses.map((m) => {
                const valor = Number(m.total);
                const altura = maxTotal > 0 ? (valor / maxTotal) * 100 : 0;
                const ativo = mesDetalhe === m.mes;
                return (
                  <button
                    key={m.mes}
                    className={`barra-col${ativo ? " ativo" : ""}`}
                    onClick={() => setMesDetalhe(ativo ? null : m.mes)}
                    title={`${MESES[m.mes - 1]}: ${eur(m.total)}`}
                  >
                    <span className="barra-valor">{valor > 0 ? eur(valor) : ""}</span>
                    <span className="barra" style={{ height: `${altura}%` }} />
                    <span className="barra-rotulo">{MESES[m.mes - 1]}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Detalhe do mês selecionado */}
          {mesDetalhe && dados.detalhe && (
            <div className="tabela-wrap">
              <table className="tabela">
                <thead>
                  <tr>
                    <th>Data</th>
                    <th>Descrição</th>
                    <th style={{ textAlign: "right" }}>Valor</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.detalhe.length === 0 ? (
                    <tr><td colSpan={3} className="muted" style={{ textAlign: "center" }}>
                      Sem despesas em {MESES[mesDetalhe - 1]}.
                    </td></tr>
                  ) : (
                    dados.detalhe.map((d) => (
                      <tr key={d.id}>
                        <td>{d.data}</td>
                        <td>{d.descricao}</td>
                        <td style={{ textAlign: "right" }}>{eur(d.valor)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <hr style={{ margin: "2.5rem 0", border: "none", borderTop: "1px solid var(--border)" }} />
      <FaturacaoObra />

      <hr style={{ margin: "2.5rem 0", border: "none", borderTop: "1px solid var(--border)" }} />
      <EquipamentosPorFuncionario />
    </section>
  );
}

// --- Relatório: faturação por obra (total + lista de autos) ---
function FaturacaoObra() {
  const [obra, setObra] = useState<string>("");
  const [dados, setDados] = useState<RelatorioFaturacaoObra | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const obras = useOpcoes<Obra>("/obras/", (o) => o.nome);

  useEffect(() => {
    if (!obra) {
      setDados(null);
      return;
    }
    setErro(null);
    api
      .get<RelatorioFaturacaoObra>(`/reports/faturacao-obra/?obra=${obra}`)
      .then((res) => setDados(res.data))
      .catch(() => setErro("Não foi possível carregar o relatório."));
  }, [obra]);

  return (
    <div>
      <h2>Faturação por obra</h2>
      <p className="subtitulo">Total faturado numa obra e os seus autos mensais.</p>
      <div className="card" style={{ margin: "1rem 0" }}>
        <label>
          Obra
          <select value={obra} onChange={(e) => setObra(e.target.value)}>
            <option value="">Selecionar…</option>
            {obras.map((o) => (
              <option key={o.valor} value={o.valor}>{o.texto}</option>
            ))}
          </select>
        </label>
      </div>

      {erro && <div className="alert-erro">{erro}</div>}

      {dados && (
        <>
          <div className="kpi-grid">
            <div className="kpi">
              <span className="kpi-icone is-info">€</span>
              <div>
                <div className="kpi-valor">{eur(dados.total)}</div>
                <div className="kpi-rotulo">Total (todos os autos)</div>
              </div>
            </div>
            <div className="kpi">
              <span className="kpi-icone is-ok">✓</span>
              <div>
                <div className="kpi-valor">{eur(dados.total_faturado)}</div>
                <div className="kpi-rotulo">Já faturado</div>
              </div>
            </div>
            <div className="kpi">
              <span className="kpi-icone is-aviso">…</span>
              <div>
                <div className="kpi-valor">{eur(dados.total_por_faturar)}</div>
                <div className="kpi-rotulo">Por faturar</div>
              </div>
            </div>
          </div>

          <div className="tabela-wrap" style={{ marginTop: "1rem" }}>
            <table className="tabela">
              <thead>
                <tr>
                  <th>Período</th>
                  <th>Descrição</th>
                  <th>Estado</th>
                  <th style={{ textAlign: "right" }}>Valor</th>
                </tr>
              </thead>
              <tbody>
                {dados.autos.length === 0 ? (
                  <tr><td colSpan={4} className="muted" style={{ textAlign: "center" }}>
                    Sem autos nesta obra.
                  </td></tr>
                ) : (
                  dados.autos.map((a) => (
                    <tr key={a.id}>
                      <td>{String(a.mes).padStart(2, "0")}/{a.ano}</td>
                      <td>{a.descricao || "—"}</td>
                      <td>{a.estado_display}</td>
                      <td style={{ textAlign: "right" }}>{eur(a.valor)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

// --- Relatório: equipamentos de um funcionário ---
function EquipamentosPorFuncionario() {
  const [func, setFunc] = useState<string>("");
  const [dados, setDados] = useState<RelatorioEquipamentosFuncionario | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const funcionarios = useOpcoes<Funcionario>("/funcionarios/", (f) => f.nome);

  useEffect(() => {
    if (!func) {
      setDados(null);
      return;
    }
    setErro(null);
    api
      .get<RelatorioEquipamentosFuncionario>(
        `/reports/equipamentos-funcionario/?funcionario=${func}`,
      )
      .then((res) => setDados(res.data))
      .catch(() => setErro("Não foi possível carregar o relatório."));
  }, [func]);

  return (
    <div>
      <h2>Equipamentos por funcionário</h2>
      <p className="subtitulo">Equipamentos à responsabilidade de um funcionário.</p>
      <div className="card" style={{ margin: "1rem 0" }}>
        <label>
          Funcionário
          <select value={func} onChange={(e) => setFunc(e.target.value)}>
            <option value="">Selecionar…</option>
            {funcionarios.map((o) => (
              <option key={o.valor} value={o.valor}>{o.texto}</option>
            ))}
          </select>
        </label>
      </div>

      {erro && <div className="alert-erro">{erro}</div>}

      {dados && (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>Equipamento</th>
                <th>Nº de série</th>
                <th>Ativo</th>
              </tr>
            </thead>
            <tbody>
              {dados.equipamentos.length === 0 ? (
                <tr><td colSpan={3} className="muted" style={{ textAlign: "center" }}>
                  {dados.funcionario_nome} não tem equipamentos à responsabilidade.
                </td></tr>
              ) : (
                dados.equipamentos.map((e) => (
                  <tr key={e.id}>
                    <td>{e.nome}</td>
                    <td>{e.numero_serie ?? "—"}</td>
                    <td>{e.ativo ? "Sim" : "Não"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

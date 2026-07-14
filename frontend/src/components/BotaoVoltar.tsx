// Botão "Voltar" para as páginas de detalhe. Volta à página anterior no
// histórico; se não houver (ex.: link direto), vai para um destino de recurso.

import { useNavigate } from "react-router-dom";

export default function BotaoVoltar({ para }: { para?: string }) {
  const navigate = useNavigate();

  function voltar() {
    // -1 = página anterior. Se a pessoa entrou por link direto e não há
    // histórico dentro da app, cai no destino indicado (ex.: a lista).
    if (window.history.length > 1) {
      navigate(-1);
    } else if (para) {
      navigate(para);
    } else {
      navigate("/");
    }
  }

  return (
    <button className="btn-voltar" onClick={voltar}>
      <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M15 18l-6-6 6-6" />
      </svg>
      Voltar
    </button>
  );
}

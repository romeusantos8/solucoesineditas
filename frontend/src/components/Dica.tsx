// Faixa de dica/informação, para orientar o utilizador (ex.: "clica no nome
// para ver detalhes"). Discreta mas visível, acima de uma tabela.

import type { ReactNode } from "react";

export default function Dica({ children }: { children: ReactNode }) {
  return (
    <div className="dica" role="note">
      <span className="dica-icone" aria-hidden="true">
        <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5M12 8h.01" />
        </svg>
      </span>
      <span>{children}</span>
    </div>
  );
}

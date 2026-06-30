// Janela modal: conteúdo centrado sobre um fundo desfocado (overlay).
//
// Fecha ao clicar no fundo, no botão ✕, ou ao premir Escape. O clique dentro do
// cartão não propaga para o overlay (senão fechava ao interagir com o form).

import { useEffect, type ReactNode } from "react";

interface ModalProps {
  aberto: boolean;
  titulo: string;
  onFechar: () => void;
  children: ReactNode;
}

export default function Modal({ aberto, titulo, onFechar, children }: ModalProps) {
  // Fechar com a tecla Escape enquanto o modal está aberto.
  useEffect(() => {
    if (!aberto) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onFechar();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [aberto, onFechar]);

  if (!aberto) return null;

  return (
    <div className="modal-overlay" onClick={onFechar}>
      <div
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>{titulo}</h2>
          <button className="btn-link modal-fechar" onClick={onFechar} aria-label="Fechar">
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

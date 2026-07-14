// Ícones SVG inline (stroke), reutilizáveis. Herdam a cor via currentColor e o
// tamanho via prop. Conjunto mínimo para a navegação e os tipos de alerta.

interface IconeProps {
  size?: number;
}

function base(size: number) {
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
}

export function IconeAlertas({ size = 20 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M12 9v4M12 17h.01" />
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
    </svg>
  );
}

export function IconeViaturas({ size = 20 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M5 17h14M3 13l2-6h14l2 6M5 17a2 2 0 1 0 4 0M15 17a2 2 0 1 0 4 0" />
      <path d="M3 13h18v3a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-3Z" />
    </svg>
  );
}

export function IconeEquipamentos({ size = 20 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4l-6 6a1.5 1.5 0 0 0 2 2l6-6a4 4 0 0 0 5.4-5.4l-2.5 2.5-2-2 2.5-2.5Z" />
    </svg>
  );
}

export function IconeFuncionarios({ size = 20 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3.5 19a5.5 5.5 0 0 1 11 0M16 6.5a3 3 0 0 1 0 5.5M18 19a5 5 0 0 0-3-4.6" />
    </svg>
  );
}

export function IconeClientes({ size = 20 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M4 21V5a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v16" />
      <path d="M13 9h6a1 1 0 0 1 1 1v11M3 21h18M7 8h2M7 12h2M7 16h2M16 13h1M16 17h1" />
    </svg>
  );
}

export function IconeObras({ size = 20 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M3 21h18M5 21V8l5-3 5 3M5 12h10M10 21v-4h4v4" />
      <path d="M15 21V11l4 2v8" />
    </svg>
  );
}

export function IconeRelatorios({ size = 20 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />
    </svg>
  );
}

// --- Tipos de alerta ---
export function IconeSeguro({ size = 16 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M12 3 5 6v5c0 4 3 7 7 9 4-2 7-5 7-9V6l-7-3Z" />
      <path d="M9.5 12l1.8 1.8 3.2-3.6" />
    </svg>
  );
}

export function IconeInspecao({ size = 16 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M9 4h6a1 1 0 0 1 1 1v0a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v0a1 1 0 0 1 1-1Z" />
      <path d="M8 5H6a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2" />
      <path d="m9 13 1.5 1.5L14 11" />
    </svg>
  );
}

export function IconeCertificado({ size = 16 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <circle cx="12" cy="9" r="5" />
      <path d="m9 13-1 7 4-2 4 2-1-7" />
    </svg>
  );
}

export function IconeFichaMedica({ size = 16 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M19 14a7 7 0 1 1-14 0c0-3 2-5 2-7a5 5 0 0 1 10 0c0 2 2 4 2 7Z" />
      <path d="M12 8v6M9 11h6" />
    </svg>
  );
}

// --- Utilitários ---
export function IconeLupa({ size = 16 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.2-3.2" />
    </svg>
  );
}

export function IconeMenu({ size = 22 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

export function IconeSair({ size = 16 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M9 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3M16 17l5-5-5-5M21 12H9" />
    </svg>
  );
}

export function IconeOk({ size = 24 }: IconeProps) {
  return (
    <svg {...base(size)}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

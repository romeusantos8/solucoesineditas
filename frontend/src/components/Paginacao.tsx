// Botões Anterior/Seguinte para listas paginadas (usa os campos do useCrud).
// Não mostra nada quando tudo cabe numa página.

interface PaginacaoProps {
  pagina: number;
  total: number;
  temProxima: boolean;
  onMudar: (pagina: number) => void;
}

export default function Paginacao({ pagina, total, temProxima, onMudar }: PaginacaoProps) {
  if (pagina <= 1 && !temProxima) return null;
  return (
    <div className="paginacao">
      <span className="info">
        Página {pagina} — {total} no total
      </span>
      <button className="btn-secundario" onClick={() => onMudar(pagina - 1)} disabled={pagina <= 1}>
        Anterior
      </button>
      <button className="btn-secundario" onClick={() => onMudar(pagina + 1)} disabled={!temProxima}>
        Seguinte
      </button>
    </div>
  );
}

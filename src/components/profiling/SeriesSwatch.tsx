// Opacidade do preenchimento das áreas do radar. A legenda usa a mesma, para a cor
// da bolinha ser a que se vê no gráfico (área translúcida com contorno sólido).
export const RADAR_FILL_OPACITY = 0.5;

function withAlpha(hex: string, alpha: number) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex);
  if (!m) return hex;
  const n = parseInt(m[1], 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}

type SeriesSwatchProps = {
  color: string;
  /** Diâmetro em px. */
  size?: number;
  className?: string;
};

// Marcador de legenda com a mesma aparência da área do radar: preenchimento translúcido e contorno sólido.
export default function SeriesSwatch({ color, size = 12, className = "" }: SeriesSwatchProps) {
  return (
    <span
      aria-hidden="true"
      className={`inline-block flex-shrink-0 rounded-full ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: withAlpha(color, RADAR_FILL_OPACITY),
        border: `2px solid ${color}`,
        boxSizing: "border-box",
      }}
    />
  );
}

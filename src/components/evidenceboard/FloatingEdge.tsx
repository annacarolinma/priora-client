import {
  BaseEdge,
  Position,
  getSmoothStepPath,
  getStraightPath,
  useInternalNode,
  type EdgeProps,
  type InternalNode,
} from '@xyflow/react';

type Box = { left: number; top: number; right: number; bottom: number; cx: number; cy: number };

function box(node: InternalNode): Box {
  const { x, y } = node.internals.positionAbsolute;
  const w = node.measured.width ?? 0;
  const h = node.measured.height ?? 0;
  return { left: x, top: y, right: x + w, bottom: y + h, cx: x + w / 2, cy: y + h / 2 };
}

// Ponto médio do lado — é onde ficam os pontos de conexão (e os vértices do
// losango / extremos do círculo), igual aos conectores do draw.io e do Figma.
function anchor(b: Box, side: Position) {
  switch (side) {
    case Position.Top:
      return { x: b.cx, y: b.top };
    case Position.Bottom:
      return { x: b.cx, y: b.bottom };
    case Position.Left:
      return { x: b.left, y: b.cy };
    default:
      return { x: b.right, y: b.cy };
  }
}

// Escolhe o par de lados que se encaram: se os nós estão mais separados na
// horizontal, a seta sai pela lateral; senão, por cima/baixo.
function pickSides(s: Box, t: Box): [Position, Position] {
  const gapX = Math.max(t.left - s.right, s.left - t.right);
  const gapY = Math.max(t.top - s.bottom, s.top - t.bottom);

  if (gapX >= gapY) {
    return t.cx >= s.cx ? [Position.Right, Position.Left] : [Position.Left, Position.Right];
  }
  return t.cy >= s.cy ? [Position.Bottom, Position.Top] : [Position.Top, Position.Bottom];
}

export default function FloatingEdge({ id, source, target, markerEnd, style, selected }: EdgeProps) {
  const sourceNode = useInternalNode(source);
  const targetNode = useInternalNode(target);
  if (!sourceNode || !targetNode || source === target) return null;

  const s = box(sourceNode);
  const t = box(targetNode);
  const [sourcePosition, targetPosition] = pickSides(s, t);
  const sp = anchor(s, sourcePosition);
  const tp = anchor(t, targetPosition);

  // Nós quase alinhados: um "degrau" de poucos pixels fica feio, então vai reto.
  const horizontal = sourcePosition === Position.Left || sourcePosition === Position.Right;
  const misalign = horizontal ? Math.abs(sp.y - tp.y) : Math.abs(sp.x - tp.x);
  const [path] = misalign < 12
    ? getStraightPath({ sourceX: sp.x, sourceY: sp.y, targetX: tp.x, targetY: tp.y })
    : // conector ortogonal com cantos arredondados
      getSmoothStepPath({
    sourceX: sp.x,
    sourceY: sp.y,
    sourcePosition,
    targetX: tp.x,
    targetY: tp.y,
    targetPosition,
    borderRadius: 10,
    offset: 24,
  });

  return (
    <BaseEdge
      id={id}
      path={path}
      markerEnd={markerEnd}
      interactionWidth={16}
      style={{ ...style, ...(selected ? { stroke: '#a78bfa', strokeWidth: 2 } : null) }}
    />
  );
}

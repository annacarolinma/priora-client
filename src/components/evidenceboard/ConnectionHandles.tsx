import { Handle, Position } from '@xyflow/react';

const SIDES = [Position.Top, Position.Right, Position.Bottom, Position.Left];

// Pontos de conexão nos quatro lados. Com ConnectionMode.Loose, todos podem
// iniciar e receber setas; o FloatingEdge decide por qual lado a seta passa.
export default function ConnectionHandles({ className = 'bg-zinc-400! w-2! h-2!' }: { className?: string }) {
  return (
    <>
      {SIDES.map((side) => (
        <Handle key={side} id={side} type="source" position={side} className={className} />
      ))}
    </>
  );
}

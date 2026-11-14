import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { apiFetch } from '@/lib/api';
import BoardSkeleton from "@/components/evidenceboard/BoardSkeleton";
import { useCaseRole } from '@/hooks/useCaseRole';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  useConnection,
  ConnectionMode,
  ConnectionLineType,
  MarkerType,
  type Connection,
  type DefaultEdgeOptions,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import '../../components/evidenceboard/board.css';

import TextBoxNode from '../../components/evidenceboard/TextBoxNode';
import ImageBoxNode from '../../components/evidenceboard/ImageBoxNode';
import NoteNode from '../../components/evidenceboard/NoteNode';
import FloatingEdge from '../../components/evidenceboard/FloatingEdge';
import BoardToolbar, { type ShapeTool } from '../../components/evidenceboard/BoardToolbar';
import type { BoardNode, BoardEdge } from '../../components/evidenceboard/types';

const nodeTypes = {
  textBox: TextBoxNode,
  imageBox: ImageBoxNode,
  note: NoteNode,
};

const edgeTypes = { floating: FloatingEdge };

const EDGE_COLOR = '#a1a1aa';

const defaultEdgeOptions: DefaultEdgeOptions = {
  type: 'floating',
  style: { stroke: EDGE_COLOR, strokeWidth: 1.5 },
  markerEnd: { type: MarkerType.ArrowClosed, color: EDGE_COLOR, width: 12, height: 12 },
};

// Setas salvas antes usavam type 'step' presas a handles fixos (saíam sempre pela
// direita/baixo). Converte para a seta flutuante, que escolhe o lado sozinha.
function toFloatingEdge(edge: BoardEdge): BoardEdge {
  return {
    ...edge,
    ...defaultEdgeOptions,
    sourceHandle: null,
    targetHandle: null,
  };
}

function BoardCanvas({
  initialNodes,
  initialEdges,
  onSave,
  isSaving,
  caseId,
  readOnly,
}: {
  initialNodes: BoardNode[];
  initialEdges: BoardEdge[];
  onSave: (nodes: BoardNode[], edges: BoardEdge[]) => void;
  isSaving: boolean;
  caseId: string;
  readOnly: boolean;
}) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();
  // mostra todos os pontos de conexão enquanto uma seta está sendo arrastada
  const isConnecting = useConnection((c) => c.inProgress);

  // quando o fetch do backend terminar e initialNodes/Edges chegarem, sincroniza o canvas
  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges.map(toFloatingEdge));
  }, [initialEdges, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) =>
      setEdges((eds) => addEdge(toFloatingEdge({ ...connection, id: crypto.randomUUID() }), eds)),
    [setEdges]
  );

  const isValidConnection = useCallback(
    (connection: Connection | BoardEdge) => connection.source !== connection.target,
    []
  );

  const handleAddShape = useCallback(
    (tool: ShapeTool) => {
      // posiciona o novo node perto do centro do canvas visível
      const bounds = wrapperRef.current?.getBoundingClientRect();
      const center = bounds
        ? screenToFlowPosition({ x: bounds.left + bounds.width / 2, y: bounds.top + bounds.height / 2 })
        : { x: 250, y: 250 };

      const nodeId = crypto.randomUUID();
      let newNode: BoardNode;

      switch (tool) {
        case 'image':
          newNode = {
            id: nodeId,
            type: "imageBox",
            position: center,
            data: {
                imageUrl: "",
                caption: "",
                caseId: caseId,
            },
          };
          break;

        case 'text':
          // label solto, sem caixa ao redor (ex: "Quem é?")
          newNode = {
            id: nodeId,
            type: 'note',
            position: center,
            data: { text: '' },
          };
          break;

        case 'note':
          // post-it de verdade: papel colorido, sem forma/caixa
          newNode = {
              id: nodeId,
            type: 'textBox',
            position: center,
            data: { label: '', color: '#fde68a', variant: 'postit' },
          };
          break;

        case 'circle':
          newNode = {
              id: nodeId,
            type: 'textBox',
            position: center,
            data: { label: '', color: '#9b6ff0', shape: 'circle' },
          };
          break;

        case 'diamond':
          newNode = {
              id: nodeId,
            type: 'textBox',
            position: center,
            data: { label: '', color: '#9b6ff0', shape: 'diamond' },
          };
          break;

        case 'arrow':
          // não cria node: conexões são feitas arrastando de um handle a outro
          toast('Arraste de um ponto de conexão a outro para criar uma seta.');
          return;

        // 'rectangle'
        default:
          newNode = {
            id: nodeId,
            type: 'textBox',
            position: center,
            data: { label: '', color: '#9b6ff0', shape: 'rectangle' },
          };
      }

      setNodes((nds) => [...nds, newNode]);
    },
    [screenToFlowPosition, setNodes]
  );

  const handleDeleteSelected = useCallback(() => {
    setNodes((nds) => nds.filter((n) => !n.selected));
    setEdges((eds) => eds.filter((e) => !e.selected));
  }, [setNodes, setEdges]);

  const handleSaveClick = useCallback(() => {
    onSave(nodes as BoardNode[], edges);
  }, [nodes, edges, onSave]);

  return (
    // Altura da área abaixo da AppTopBar (h-16), para o quadro não rolar e esconder a toolbar
    <div className="flex flex-col h-[calc(100dvh-4rem)] bg-zinc-950">
      {readOnly ? (
        <div className="px-4 py-2 text-xs text-zinc-400 border-b border-zinc-800 bg-zinc-900">
          Modo somente leitura: seu papel neste caso não permite editar o quadro.
        </div>
      ) : (
        <BoardToolbar
          onAddShape={handleAddShape}
          onSave={handleSaveClick}
          onDeleteSelected={handleDeleteSelected}
          isSaving={isSaving}
        />
      )}

      <div ref={wrapperRef} className={`evidence-board flex-1 ${isConnecting ? 'is-connecting' : ''}`}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          isValidConnection={isValidConnection}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          connectionMode={ConnectionMode.Loose}
          connectionLineType={ConnectionLineType.SmoothStep}
          connectionLineStyle={{ stroke: EDGE_COLOR, strokeWidth: 1.5 }}
          nodesDraggable={!readOnly}
          nodesConnectable={!readOnly}
          deleteKeyCode={readOnly ? null : 'Backspace'}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} color="#3f3f46" gap={22} size={1} />
          <Controls className="bg-zinc-900! border-zinc-700 [&>button]:bg-zinc-900! [&>button]:border-zinc-700! [&>button]:text-zinc-300!" />
        </ReactFlow>
      </div>
    </div>
  );
}

export default function EvidenceBoard() {
  // mesma chave "id" que o TopBar.tsx já usa pra buscar o caso
  const { id } = useParams<{ id: string }>();
  const { canEdit, loading: roleLoading } = useCaseRole(id);

  const [nodes, setNodes] = useState<BoardNode[]>([]);
  const [edges, setEdges] = useState<BoardEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    async function loadBoard() {
      setLoading(true);
      try {
        const response = await apiFetch(`/cases/${id}/board`);

        if (response.status === 404) {
          if (!cancelled) {
            setNodes([]);
            setEdges([]);
          }
          return;
        }

        if (!response.ok) throw new Error('Erro ao carregar o quadro investigativo.');

        const data = await response.json();
        if (!cancelled) {
          setNodes(data.nodes ?? []);
          setEdges(data.edges ?? []);
        }
      } catch (err: unknown) {
        toast.error(err instanceof Error ? err.message : 'Erro ao carregar o quadro.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadBoard();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleSave = useCallback(
    async (updatedNodes: BoardNode[], updatedEdges: BoardEdge[]) => {
      if (!id) return;
      setIsSaving(true);
      try {
        const response = await apiFetch(`/cases/${id}/board`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ nodes: updatedNodes, edges: updatedEdges }),
        });
        if (!response.ok) throw new Error('Erro ao salvar o quadro investigativo.');
        toast.success('Quadro salvo com sucesso!');
      } catch (err: unknown) {
        toast.error(err instanceof Error ? err.message : 'Erro ao salvar o quadro.');
      } finally {
        setIsSaving(false);
      }
    },
    [id]
  );

  if (loading || roleLoading) return <BoardSkeleton />;

  

  return (
    <ReactFlowProvider>
      <BoardCanvas
        initialNodes={nodes}
        initialEdges={edges}
        onSave={handleSave}
        isSaving={isSaving}
        caseId={id!}
        readOnly={!canEdit}
      />
    </ReactFlowProvider>
  );
}



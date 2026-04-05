import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap,
  useNodesState, useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { GitMerge, RefreshCw, Server, User, Cpu, Globe, ShieldAlert } from 'lucide-react';
import { useAuth } from '../store/AuthContext';

// ── Node type coloring by asset class ────────────────────────────────────────
const NODE_STYLE = {
  Host:    { bg: 'rgba(59,111,227,0.12)',  border: '#3B6FE3', color: '#93C5FD', icon: '🖥' },
  User:    { bg: 'rgba(229,168,98,0.12)',  border: '#E5A862', color: '#FCD34D', icon: '👤' },
  Service: { bg: 'rgba(136,192,87,0.12)', border: '#88C057', color: '#BBF7D0', icon: '⚙' },
  Process: { bg: 'rgba(216,76,127,0.12)', border: '#D84C7F', color: '#F9A8D4', icon: '🔄' },
};

const getNodeStyle = (type) => NODE_STYLE[type] || NODE_STYLE.Host;

// ── Empty state shown when topology is clear / no data yet ──────────────────
function EmptyTopology({ onRefresh }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 select-none" style={{ color: '#4B5563' }}>
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
           style={{ background: '#111827', border: '1px solid #1F2937' }}>
        <GitMerge size={30} style={{ color: '#3B6FE366' }} />
      </div>
      <div className="text-center">
        <p className="h-title" style={{ color: '#6B7280' }}>No Topology Data</p>
        <p className="h-meta mt-1">
          GAGGLE-SCOUT and GAGGLE-TOPOLOGY-MAPPER<br />
          haven't indexed any assets yet.
        </p>
      </div>
      <button
        onClick={onRefresh}
        className="flex items-center gap-2 text-xs terminal px-4 py-2 rounded-lg hover:brightness-125 transition-all"
        style={{ background: '#3B6FE318', color: '#3B6FE3', border: '1px solid #3B6FE344' }}>
        <RefreshCw size={12} /> Refresh Graph
      </button>
    </div>
  );
}

// ── Mock topology seed for when the backend hasn't produced data yet ──────────
const MOCK_NODES = [
  { id: 'DC-01',        type: 'Host',    label: 'DC-01',        group: 'IT' },
  { id: '10.0.44.82',   type: 'Host',    label: '10.0.44.82',   group: 'IT' },
  { id: 'Host-DX9',     type: 'Host',    label: 'Host-DX9',     group: 'IT' },
  { id: 'MFG-PROD-01',  type: 'Host',    label: 'MFG-PROD-01',  group: 'OT' },
  { id: 'MFG-WS-01',    type: 'Host',    label: 'MFG-WS-01',    group: 'OT' },
  { id: 'j.smith',      type: 'User',    label: 'j.smith',      group: 'IT' },
  { id: 'svc-backup',   type: 'Service', label: 'svc-backup',   group: 'IT' },
  { id: '45.33.22.11',  type: 'Host',    label: '45.33.22.11 ⚠', group: 'EXT' },
];

const MOCK_EDGES = [
  { id: 'e1', source: 'j.smith',    target: 'Host-DX9',    type: 'LOGGED_INTO' },
  { id: 'e2', source: 'Host-DX9',   target: '45.33.22.11', type: 'COMMUNICATED_TCP', animated: true },
  { id: 'e3', source: '10.0.44.82', target: 'DC-01',       type: 'COMMUNICATED_SMB' },
  { id: 'e4', source: 'MFG-WS-01',  target: 'MFG-PROD-01', type: 'COMMUNICATED_MODBUS' },
  { id: 'e5', source: 'svc-backup', target: 'DC-01',       type: 'COMMUNICATED_SMB' },
];

// ── Layout helper: stagger nodes into a simple force-grid ───────────────────
function layoutNodes(rawNodes) {
  const cols = Math.ceil(Math.sqrt(rawNodes.length + 1));
  return rawNodes.map((n, i) => {
    const st = getNodeStyle(n.type);
    return {
      id: n.id,
      data: { label: `${st.icon} ${n.label}` },
      position: {
        x: 120 + (i % cols) * 200 + (Math.floor(i / cols) % 2) * 60,
        y: 80  + Math.floor(i / cols) * 140,
      },
      style: {
        background: st.bg,
        border: `1px solid ${st.border}`,
        color: st.color,
        fontSize: 11,
        fontFamily: 'JetBrains Mono',
        borderRadius: 8,
        padding: '6px 10px',
        boxShadow: `0 0 0 0 ${st.border}`,
      },
    };
  });
}

// ── Main component ─────────────────────────────────────────────────────────
export default function EntityGraph() {
  const { authenticatedFetch } = useAuth();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isMock, setIsMock] = useState(false);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);

  const fetchTopology = useCallback(async () => {
    setIsLoading(true);
    try {
      const resp = await authenticatedFetch('http://localhost:8000/api/v1/topology');
      if (resp.ok) {
        const data = await resp.json();
        const rawNodes = data.nodes || [];
        const rawEdges = data.edges || [];

        if (rawNodes.length > 0) {
          setNodes(layoutNodes(rawNodes));
          setEdges(rawEdges.map(e => ({
            id: e.id,
            source: e.source,
            target: e.target,
            label: e.type?.replace('COMMUNICATED_', '').replace('_', '/') || '',
            animated: e.type?.includes('COMMUNICATED'),
            style: { stroke: '#374151', strokeWidth: 1.5 },
            labelStyle: { fill: '#6B7280', fontSize: 9, fontFamily: 'JetBrains Mono' },
            labelBgStyle: { fill: '#0B1117', fillOpacity: 0.8 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#374151' },
          })));
          setIsMock(false);
          setNodeCount(rawNodes.length);
          setEdgeCount(rawEdges.length);
        } else {
          // Backend returned empty graph — seed with mock lab data
          throw new Error('empty');
        }
      } else {
        throw new Error('fetch failed');
      }
    } catch {
      // Graceful fallback to mock topology
      setNodes(layoutNodes(MOCK_NODES));
      setEdges(MOCK_EDGES.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.type?.replace('COMMUNICATED_', '') || '',
        animated: !!e.animated,
        style: { stroke: '#374151', strokeWidth: 1.5 },
        labelStyle: { fill: '#6B7280', fontSize: 9, fontFamily: 'JetBrains Mono' },
        labelBgStyle: { fill: '#0B1117', fillOpacity: 0.8 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#374151' },
      })));
      setIsMock(true);
      setNodeCount(MOCK_NODES.length);
      setEdgeCount(MOCK_EDGES.length);
    } finally {
      setIsLoading(false);
    }
  }, [authenticatedFetch, setNodes, setEdges]);

  useEffect(() => {
    fetchTopology();
    const id = setInterval(fetchTopology, 30000);
    return () => clearInterval(id);
  }, [fetchTopology]);

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <GitMerge size={14} style={{ color: '#3B6FE3' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            ASSET RELATIONSHIP TOPOLOGY
          </span>
          {isMock && (
            <span className="text-[10px] terminal px-2 py-0.5 rounded-full"
                  style={{ background: '#E5A86218', color: '#E5A862', border: '1px solid #E5A86244' }}>
              DEMO DATA
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* KPI pills */}
          <span className="text-xs terminal" style={{ color: '#4B5563' }}>
            <span style={{ color: '#3B6FE3' }}>{nodeCount}</span> nodes
          </span>
          <span className="text-xs terminal" style={{ color: '#4B5563' }}>
            <span style={{ color: '#88C057' }}>{edgeCount}</span> edges
          </span>
          <div className="w-px h-4" style={{ background: '#1F2937' }} />
          <button
            onClick={fetchTopology}
            className={`p-1.5 rounded hover:bg-white/5 transition-colors ${isLoading ? 'animate-spin' : ''}`}
            title="Refresh graph">
            <RefreshCw size={13} style={{ color: isLoading ? '#3B6FE3' : '#6B7280' }} />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 px-5 py-2 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#080c12' }}>
        {Object.entries(NODE_STYLE).map(([type, st]) => (
          <div key={type} className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-sm" style={{ background: st.border, opacity: 0.8 }} />
            <span className="text-[10px] terminal" style={{ color: '#6B7280' }}>{type}</span>
          </div>
        ))}
        <div className="ml-auto flex items-center gap-1.5">
          <div className="w-6 h-px border-t border-dashed" style={{ borderColor: '#3B6FE3' }} />
          <span className="text-[10px] terminal" style={{ color: '#6B7280' }}>Animated = active comms</span>
        </div>
      </div>

      {/* Graph Canvas */}
      <div className="flex-1 relative">
        {!isLoading && nodes.length === 0 ? (
          <EmptyTopology onRefresh={fetchTopology} />
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.3}
            proOptions={{ hideAttribution: true }}>

            <Background color="#1F2937" gap={24} size={1} />

            <Controls
              style={{ background: '#111827', border: '1px solid #1F2937' }}
              showInteractive={false}
            />

            <MiniMap
              style={{ background: '#0d1117', border: '1px solid #1F2937', borderRadius: 8 }}
              nodeColor={(n) => {
                const border = n.style?.border || '';
                if (border.includes('3B6FE3')) return '#3B6FE3';
                if (border.includes('E5A862')) return '#E5A862';
                if (border.includes('88C057')) return '#88C057';
                return '#D84C7F';
              }}
              maskColor="rgba(11,17,23,0.6)"
            />
          </ReactFlow>
        )}

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30 backdrop-blur-sm z-10">
            <div className="flex flex-col items-center gap-3">
              <RefreshCw className="animate-spin" size={24} style={{ color: '#3B6FE3' }} />
              <p className="text-xs terminal" style={{ color: '#3B6FE3' }}>Mapping Neural Links...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

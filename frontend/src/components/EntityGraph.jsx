import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap, useNodesState, useEdgesState, addEdge } from 'reactflow';
import 'reactflow/dist/style.css';
import { Filter, Maximize2, Layers, RefreshCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const FILTERS = ['Host', 'Process', 'User', 'Service'];

export default function EntityGraph() {
  const { authenticatedFetch } = useAuth();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeFilters, setActiveFilters] = useState(['Host', 'Process', 'User', 'Service']);

  const fetchTopology = useCallback(async () => {
    setIsLoading(true);
    try {
      const resp = await authenticatedFetch('/api/v1/topology');
      if (resp.ok) {
        const data = await resp.json();
        
        // Map backend nodes to ReactFlow format
        const rfNodes = data.nodes.map((n, idx) => ({
          id: n.id,
          data: { label: n.label },
          position: { x: 100 + (idx * 200) % 600, y: 100 + Math.floor(idx / 3) * 150 },
          style: {
            background: n.type === 'Host' ? 'rgba(59,111,227,0.15)' : 
                       n.type === 'User' ? 'rgba(229,168,98,0.15)' : 
                       'rgba(216,76,127,0.15)',
            border: `1px solid ${n.type === 'Host' ? '#3B6FE3' : n.type === 'User' ? '#E5A862' : '#D84C7F'}`,
            color: n.type === 'Host' ? '#93C5FD' : n.type === 'User' ? '#FCD34D' : '#F9A8D4',
            fontSize: 11,
            borderRadius: 6,
            padding: '4px 8px'
          }
        }));

        const rfEdges = data.edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.type,
          animated: e.type.includes('COMMUNICATED'),
          style: { stroke: '#4B5563', strokeWidth: 1.5 },
          labelStyle: { fill: '#6B7280', fontSize: 10, fontWeight: 700 }
        }));

        setNodes(rfNodes);
        setEdges(rfEdges);
      }
    } catch (err) {
      console.error("Topology fetch failed:", err);
    } finally {
      setIsLoading(false);
    }
  }, [authenticatedFetch, setNodes, setEdges]);

  useEffect(() => {
    fetchTopology();
    const interval = setInterval(fetchTopology, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [fetchTopology]);

  const toggleFilter = (f) => setActiveFilters(prev =>
    prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
  );

  const filterColors = { Host: '#3B6FE3', Process: '#D84C7F', User: '#E5A862', Service: '#88C057' };

  return (
    <div className="flex flex-col h-full" style={{ background: '#0d1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937' }}>
        <div>
          <p className="text-xs font-bold tracking-widest text-emerald-500">RELATIONSHIP TOPOLOGY</p>
          <p className="text-[10px] terminal text-gray-500 uppercase">Live Institutional Memory</p>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={fetchTopology}
            className={`p-1.5 rounded hover:bg-white/5 transition-colors ${isLoading ? 'animate-spin text-emerald-500' : 'text-gray-500'}`}
          >
            <RefreshCw size={13} />
          </button>
          <button className="p-1.5 rounded hover:bg-white/5 transition-colors" title="Filters">
            <Filter size={13} style={{ color: '#6B7280' }} />
          </button>
          <button className="p-1.5 rounded hover:bg-white/5 transition-colors" title="Fullscreen">
            <Maximize2 size={13} style={{ color: '#6B7280' }} />
          </button>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#1F2937" gap={20} size={1} />
          <Controls
            style={{ background: '#111827', border: '1px solid #1F2937', color: '#6B7280' }}
          />
          <MiniMap
            style={{ background: '#0d1117', border: '1px solid #1F2937' }}
            nodeColor={(n) => {
              if (n.style?.border?.includes('3B6FE3')) return '#3B6FE3';
              if (n.style?.border?.includes('E5A862')) return '#E5A862';
              return '#D84C7F';
            }}
            maskColor="rgba(11,17,23,0.5)"
          />
        </ReactFlow>
        
        {isLoading && nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm z-10">
            <div className="flex flex-col items-center gap-3">
              <RefreshCw className="animate-spin text-emerald-500" size={24} />
              <p className="text-xs terminal text-emerald-500">Mapping Neural Links...</p>
            </div>
          </div>
        )}
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-2 px-3 py-2 border-t flex-shrink-0"
        style={{ borderColor: '#1F2937' }}>
        {FILTERS.map(f => (
          <button key={f} onClick={() => toggleFilter(f)}
            className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-full transition-all terminal"
            style={{
              background: activeFilters.includes(f) ? `${filterColors[f]}22` : 'transparent',
              border: `1px solid ${activeFilters.includes(f) ? filterColors[f] : '#374151'}`,
              color: activeFilters.includes(f) ? filterColors[f] : '#6B7280',
            }}>
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: filterColors[f] }}></span>
            {f}
          </button>
        ))}
      </div>
    </div>
  );
}

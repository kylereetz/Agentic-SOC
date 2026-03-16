import React, { useState } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import { Filter, Maximize2, Layers } from 'lucide-react';

const MOCK_NODES = [
  { id: '1', position: { x: 180, y: 120 }, data: { label: '192.168.1.105' }, type: 'default',
    style: { background: 'rgba(59,111,227,0.15)', border: '1px solid #3B6FE3', color: '#93C5FD', fontSize: 11, borderRadius: 6, padding: '4px 8px' } },
  { id: '2', position: { x: 380, y: 60 }, data: { label: 'svchost.exe' },
    style: { background: 'rgba(216,76,127,0.15)', border: '1px solid #D84C7F', color: '#F9A8D4', fontSize: 11, borderRadius: 6, padding: '4px 8px' } },
  { id: '3', position: { x: 380, y: 200 }, data: { label: 'Host-DX9' },
    style: { background: 'rgba(239,68,68,0.15)', border: '1px solid #EF4444', color: '#FCA5A5', fontSize: 11, borderRadius: 6, padding: '4px 8px' } },
  { id: '4', position: { x: 120, y: 260 }, data: { label: 'KR\\admin' },
    style: { background: 'rgba(229,168,98,0.15)', border: '1px solid #E5A862', color: '#FCD34D', fontSize: 11, borderRadius: 6, padding: '4px 8px' } },
  { id: '5', position: { x: 550, y: 140 }, data: { label: 'Domain Controller' },
    style: { background: 'rgba(239,68,68,0.2)', border: '1px solid #EF4444', color: '#FCA5A5', fontSize: 11, borderRadius: 6, padding: '4px 8px', boxShadow: '0 0 10px rgba(239,68,68,0.4)' } },
];

const MOCK_EDGES = [
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#3B6FE3', strokeWidth: 1.5 } },
  { id: 'e1-3', source: '1', target: '3', style: { stroke: '#EF4444', strokeWidth: 1.5 } },
  { id: 'e4-1', source: '4', target: '1', style: { stroke: '#E5A862', strokeWidth: 1 } },
  { id: 'e3-5', source: '3', target: '5', animated: true, style: { stroke: '#EF4444', strokeWidth: 2 } },
];

const FILTERS = ['Host', 'Process', 'User', 'Service'];

export default function EntityGraph() {
  const [activeFilters, setActiveFilters] = useState(['Host', 'Process', 'User']);

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
          <p className="text-xs font-bold tracking-widest" style={{ color: '#88C057' }}>INVESTIGATION GRAPH</p>
          <p className="text-xs terminal" style={{ color: '#4B5563' }}>INC-2023-981</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-1.5 rounded hover:bg-white/5 transition-colors" title="Filters">
            <Filter size={13} style={{ color: '#6B7280' }} />
          </button>
          <button className="p-1.5 rounded hover:bg-white/5 transition-colors" title="Fullscreen">
            <Maximize2 size={13} style={{ color: '#6B7280' }} />
          </button>
          <button className="p-1.5 rounded hover:bg-white/5 transition-colors" title="Layers">
            <Layers size={13} style={{ color: '#6B7280' }} />
          </button>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={MOCK_NODES}
          edges={MOCK_EDGES}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#1F2937" gap={20} size={1} />
          <Controls
            style={{ background: '#111827', border: '1px solid #1F2937', color: '#6B7280' }}
          />
          <MiniMap
            style={{ background: '#0d1117', border: '1px solid #1F2937' }}
            nodeColor={(n) => n.style?.border?.includes('3B6FE3') ? '#3B6FE3'
              : n.style?.border?.includes('D84C7F') ? '#D84C7F'
              : n.style?.border?.includes('E5A862') ? '#E5A862' : '#EF4444'}
            maskColor="rgba(11,17,23,0.5)"
          />
        </ReactFlow>
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

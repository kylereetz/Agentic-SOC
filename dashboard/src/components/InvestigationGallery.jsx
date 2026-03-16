import React, { useState } from 'react';
import { Search, Grid, List, ChevronRight, Bot, Clock, Layers } from 'lucide-react';

const STAGES = ['New', 'Triage', 'Investigating', 'Containment', 'Eradication', 'Recovery', 'Closed'];

const STAGE_COLORS = {
  New:           '#6B7280',
  Triage:        '#3B6FE3',
  Investigating: '#D84C7F',
  Containment:   '#EF4444',
  Eradication:   '#E5A862',
  Recovery:      '#88C057',
  Closed:        '#4B5563',
};

const SEV_COLORS = {
  Critical: '#EF4444',
  High:     '#E5A862',
  Medium:   '#3B6FE3',
  Low:      '#88C057',
};

const INVESTIGATIONS = [
  { id: 'INC-2023-981', severity: 'Critical', stage: 'Investigating', progress: 62, entities: 8, agent: 'SENTINEL-01', lastActivity: '2m ago', title: 'Credential Theft Campaign' },
  { id: 'INC-2023-980', severity: 'High',     stage: 'Containment',   progress: 85, entities: 4, agent: 'HERALD-03',   lastActivity: '7m ago', title: 'SMB Lateral Movement' },
  { id: 'INC-2023-979', severity: 'Critical', stage: 'Eradication',   progress: 92, entities: 12, agent: 'SENTINEL-01', lastActivity: '14m ago', title: 'Ransomware Staging' },
  { id: 'INC-2023-978', severity: 'Medium',   stage: 'Triage',        progress: 22, entities: 2, agent: 'RECON-02',    lastActivity: '31m ago', title: 'DNS Tunneling' },
  { id: 'INC-2023-977', severity: 'High',     stage: 'Recovery',      progress: 97, entities: 6, agent: 'HERALD-03',   lastActivity: '1h ago', title: 'Pass-the-Hash Attack' },
  { id: 'INC-2023-976', severity: 'Low',      stage: 'Closed',        progress: 100, entities: 1, agent: 'RECON-02',   lastActivity: '3h ago', title: 'Port Scan Probe' },
];

function StageTrack({ stage }) {
  const idx = STAGES.indexOf(stage);
  return (
    <div className="flex items-center gap-0.5 w-full">
      {STAGES.slice(0, -1).map((s, i) => (
        <div key={s} className="flex-1 h-1 rounded-full transition-all"
          style={{ background: i <= idx ? STAGE_COLORS[stage] : '#1F2937' }} />
      ))}
    </div>
  );
}

function InvestigationCard({ inv, onClick }) {
  const sevColor = SEV_COLORS[inv.severity];
  const stageColor = STAGE_COLORS[inv.stage];

  return (
    <div
      onClick={onClick}
      className="rounded-lg p-4 cursor-pointer transition-all hover:brightness-125 flex flex-col gap-3"
      style={{ background: '#111827', border: `1px solid ${inv.severity === 'Critical' ? '#EF444433' : '#1F2937'}`,
        boxShadow: inv.severity === 'Critical' ? '0 0 12px rgba(239,68,68,0.08)' : 'none' }}>

      {/* Top row */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs terminal" style={{ color: '#4B5563' }}>{inv.id}</p>
          <p className="text-sm font-semibold mt-0.5" style={{ color: '#E2E8F0' }}>{inv.title}</p>
        </div>
        <span className="text-xs terminal px-2 py-0.5 rounded"
          style={{ background: `${sevColor}18`, color: sevColor, border: `1px solid ${sevColor}33` }}>
          {inv.severity}
        </span>
      </div>

      {/* Stage Track */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between text-xs">
          <span className="terminal font-bold" style={{ color: stageColor }}>{inv.stage.toUpperCase()}</span>
          <span style={{ color: '#4B5563' }}>{inv.progress}%</span>
        </div>
        <StageTrack stage={inv.stage} />
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between text-xs" style={{ color: '#6B7280' }}>
        <div className="flex items-center gap-1.5">
          <Layers size={11} />
          <span>{inv.entities} entities</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Bot size={11} style={{ color: '#D84C7F' }} />
          <span style={{ color: '#D84C7F' }}>{inv.agent}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock size={11} />
          <span>{inv.lastActivity}</span>
        </div>
      </div>

      {/* CTA */}
      <button className="w-full text-xs terminal py-1.5 rounded flex items-center justify-center gap-1.5 transition-all hover:brightness-125"
        style={{ background: '#3B6FE318', color: '#3B6FE3', border: '1px solid #3B6FE333' }}>
        View Evidence <ChevronRight size={12} />
      </button>
    </div>
  );
}

export default function InvestigationGallery({ onOpenInvestigation }) {
  const [search, setSearch] = useState('');
  const [filterStage, setFilterStage] = useState('All');
  const [view, setView] = useState('grid');

  const filtered = INVESTIGATIONS.filter(i =>
    (filterStage === 'All' || i.stage === filterStage) &&
    (!search || i.title.toLowerCase().includes(search.toLowerCase()) || i.id.includes(search))
  );

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>INVESTIGATIONS</span>
        <span className="text-xs terminal px-2 py-0.5 rounded-full"
          style={{ background: '#3B6FE322', color: '#3B6FE3', border: '1px solid #3B6FE344' }}>
          {filtered.length} active
        </span>

        <div className="flex-1 relative ml-4 max-w-md">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#4B5563' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search investigations..."
            className="w-full text-xs py-1.5 pl-8 pr-3 rounded terminal focus:outline-none"
            style={{ background: '#111827', border: '1px solid #1F2937', color: '#9CA3AF' }} />
        </div>

        <div className="ml-auto flex items-center gap-1">
          <button onClick={() => setView('grid')} className="p-1.5 rounded hover:bg-white/5 transition-colors"
            style={{ color: view === 'grid' ? '#3B6FE3' : '#6B7280' }}><Grid size={14} /></button>
          <button onClick={() => setView('list')} className="p-1.5 rounded hover:bg-white/5 transition-colors"
            style={{ color: view === 'list' ? '#3B6FE3' : '#6B7280' }}><List size={14} /></button>
        </div>
      </div>

      {/* Stage filter */}
      <div className="flex items-center gap-2 px-4 py-2 border-b flex-shrink-0 overflow-x-auto"
        style={{ borderColor: '#1F2937' }}>
        {['All', ...STAGES].map(s => (
          <button key={s} onClick={() => setFilterStage(s)}
            className="flex-shrink-0 text-xs terminal px-3 py-1 rounded-full transition-all"
            style={{
              background: filterStage === s ? `${STAGE_COLORS[s] || '#FFFFFF'}18` : 'transparent',
              color: filterStage === s ? (STAGE_COLORS[s] || '#E2E8F0') : '#6B7280',
              border: `1px solid ${filterStage === s ? (STAGE_COLORS[s] || '#6B7280') + '55' : 'transparent'}`,
            }}>
            {s}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className={`flex-1 overflow-y-auto p-4 ${view === 'grid' ? 'grid gap-4' : 'flex flex-col gap-2'}`}
        style={view === 'grid' ? { gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' } : {}}>
        {filtered.map(inv => (
          <InvestigationCard key={inv.id} inv={inv} onClick={() => onOpenInvestigation?.(inv)} />
        ))}
      </div>
    </div>
  );
}

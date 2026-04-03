import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, ChevronUp, Brain, Zap, Eye, AlertCircle, Clock, Check } from 'lucide-react';
import { useSOC, ENTITY_DB } from '../store/SOCContext';

const TYPE_CONFIG = {
  THOUGHT:     { color: '#D84C7F', icon: Brain, badge: 'THOUGHT' },
  ACTION:      { color: '#3B6FE3', icon: Zap,   badge: 'ACTION'  },
  OBSERVATION: { color: '#88C057', icon: Eye,   badge: 'OBSERVATION' },
};

const STATUS_LABELS = {
  ACTIVE:   { color: '#88C057', label: 'Thinking',          pulse: true  },
  WAITING:  { color: '#E5A862', label: 'Waiting for Human', pulse: false },
  COMPLETE: { color: '#4B5563', label: 'Completed',         pulse: false },
};

// ── Inline entity token — clickable ───────────────────────────────────
function EntityToken({ name }) {
  const { clickEntity } = useSOC();
  const isKnown = !!ENTITY_DB[name];
  return (
    <button
      onClick={() => isKnown && clickEntity(name)}
      className="inline-flex items-center terminal px-1.5 py-0.5 rounded text-xs mx-0.5 hover:brightness-125 transition-all"
      style={{
        background: isKnown ? '#3B6FE322' : '#FFFFFF08',
        color:      isKnown ? '#93C5FD'   : '#9CA3AF',
        border:     `1px solid ${isKnown ? '#3B6FE344' : '#1F2937'}`,
        cursor:     isKnown ? 'pointer'   : 'default',
      }}
      title={isKnown ? `View entity: ${name}` : name}>
      {name}
    </button>
  );
}

// Replace entity names with clickable tokens in text
function EntityifiedText({ text, entities = [] }) {
  if (!text) return null;
  if (!entities.length) return <span>{text}</span>;

  const parts = [];
  let remaining = text;
  for (const entity of entities) {
    const idx = remaining.indexOf(entity);
    if (idx === -1) continue;
    if (idx > 0) parts.push(<span key={`pre-${entity}`}>{remaining.slice(0, idx)}</span>);
    parts.push(<EntityToken key={entity} name={entity} />);
    remaining = remaining.slice(idx + entity.length);
  }
  if (remaining) parts.push(<span key="tail">{remaining}</span>);
  return <>{parts}</>;
}

// ── A single timeline entry ───────────────────────────────────────────
function TimelineEntry({ event, isNew }) {
  const { setExplainEvent, entityFilter } = useSOC();
  const [expanded, setExpanded] = useState(false);
  const cfg = TYPE_CONFIG[event.type] || TYPE_CONFIG.THOUGHT;
  const Icon = cfg.icon;

  const isFiltered = entityFilter && event.entities && !event.entities.includes(entityFilter);

  return (
    <div
      className={`relative pl-8 transition-all duration-300 ${isNew ? 'animate-slide-in' : ''} ${isFiltered ? 'opacity-25' : ''}`}
      style={{ '--tw-translate-x': isNew ? '-8px' : '0px' }}>
      {/* Connector line */}
      <div className="absolute left-3 top-0 bottom-0 w-px" style={{ background: '#1F2937' }} />

      {/* Icon bubble */}
      <div className="absolute left-1 top-3 w-5 h-5 rounded-full flex items-center justify-center z-10"
        style={{ background: cfg.color + '22', border: `1.5px solid ${cfg.color}` }}>
        <Icon size={10} style={{ color: cfg.color }} />
      </div>

      {/* Card */}
      <div className="mb-2 rounded-lg overflow-hidden cursor-pointer hover:brightness-110 transition-all"
        style={{ background: '#111827', border: `1px solid ${event.isPending ? '#E5A86255' : '#1F2937'}` }}>

        {/* Card header — click to expand */}
        <div className="flex items-start gap-2 p-3" onClick={() => setExpanded(v => !v)}>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="text-xs font-bold terminal" style={{ color: cfg.color }}>{cfg.badge}</span>
              <span className="text-xs terminal px-1.5 py-0.5 rounded"
                style={{ background: '#D84C7F18', color: '#D84C7F', border: '1px solid #D84C7F22' }}>
                {event.agent}
              </span>
              {event.isPending && (
                <span className="flex items-center gap-1 text-xs terminal px-1.5 py-0.5 rounded"
                  style={{ background: '#E5A86218', color: '#E5A862', border: '1px solid #E5A86233' }}>
                  <AlertCircle size={9} className="animate-pulse" /> AWAITING APPROVAL
                </span>
              )}
              <span className="ml-auto text-xs terminal" style={{ color: '#4B5563' }}>{event.timestamp}</span>
            </div>

            {/* Content or code */}
            {event.content && (
              <p className="text-xs leading-relaxed" style={{ color: '#9CA3AF' }}>
                <EntityifiedText text={event.content} entities={event.entities} />
              </p>
            )}
            {event.code && (
              <pre className="text-xs terminal p-2 rounded mt-1 overflow-x-auto"
                style={{ background: '#0B1117', color: '#93C5FD', border: '1px solid #1F2937' }}>
                {event.code}
              </pre>
            )}
          </div>
          <div className="flex flex-col items-end gap-1.5 flex-shrink-0 ml-2">
            <div className="flex items-center gap-1 text-xs terminal" style={{ color: '#4B5563' }}>
              <Clock size={9} />{event.duration}
            </div>
            {expanded ? <ChevronUp size={12} style={{ color: '#4B5563' }} /> : <ChevronDown size={12} style={{ color: '#4B5563' }} />}
          </div>
        </div>

        {/* Expanded detail */}
        {expanded && (
          <div className="px-3 pb-3 border-t space-y-3" style={{ borderColor: '#1F2937' }}>
            <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
              <div>
                <p className="terminal" style={{ color: '#4B5563' }}>MITRE TTP</p>
                <p className="terminal mt-0.5" style={{ color: '#D84C7F' }}>{event.mitre || '—'}</p>
              </div>
              <div>
                <p className="terminal" style={{ color: '#4B5563' }}>CONFIDENCE</p>
                <p className="terminal mt-0.5 font-bold"
                  style={{ color: event.confidence >= 80 ? '#88C057' : '#E5A862' }}>
                  {event.confidence}%
                </p>
              </div>
            </div>

            {/* Tool */}
            {event.tool && (
              <div className="flex items-center gap-1.5 text-xs">
                <Zap size={10} style={{ color: '#3B6FE3' }} />
                <span className="terminal" style={{ color: '#6B7280' }}>Tool:</span>
                <code className="terminal" style={{ color: '#93C5FD' }}>{event.tool}</code>
              </div>
            )}

            {/* Entities referenced */}
            {event.entities?.length > 0 && (
              <div>
                <p className="text-xs terminal mb-1" style={{ color: '#4B5563' }}>ENTITIES</p>
                <div className="flex flex-wrap gap-1.5">
                  {event.entities.map(en => <EntityToken key={en} name={en} />)}
                </div>
              </div>
            )}

            {/* Explain button */}
            <button
              onClick={(e) => { e.stopPropagation(); setExplainEvent(event); }}
              className="flex items-center gap-1.5 text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
              style={{ background: '#D84C7F18', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
              <Brain size={11} /> Explain This Reasoning
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Static seed events (shown before live stream) ─────────────────────
const SEED_EVENTS = [
  { id: 'SEED-1', type: 'THOUGHT',    agent: 'SENTINEL-01', timestamp: '14:02:10.452', content: 'Detecting anomalous PowerShell execution with base64 encoded payload from svchost.exe. Correlating with recent credential dumping attempts on Host-DX9.',    entities: ['svchost.exe', 'Host-DX9'],         mitre: 'T1059.001', confidence: 89, tool: 'process_monitor',   duration: '1.2s', evidence: ['EVD-001'], reasoning: 'PowerShell execution with -enc flag is a strong indicator of malicious scripting. Process tree from svchost.exe parent is abnormal.' },
  { id: 'SEED-2', type: 'ACTION',     agent: 'SENTINEL-01', timestamp: '14:02:12.108', content: null, code: 'isolate_host --id "Host-DX9" --mode "quarantine"',                    entities: ['Host-DX9'],                          mitre: 'T1562',     confidence: 95, tool: 'containment_api',  duration: '0.3s', evidence: [],          reasoning: 'Host isolation is the fastest way to stop lateral movement. Risk score 95 exceeded the AUTONOMOUS_ACT threshold.' },
  { id: 'SEED-3', type: 'OBSERVATION',agent: 'SENTINEL-01', timestamp: '14:02:14.802', content: 'Host isolation confirmed. Inbound/Outbound traffic dropped. Process 9912 terminated. Memory dump captured for forensic analysis.',                          entities: ['Host-DX9'],                          mitre: null,        confidence: 100,tool: 'containment_api',  duration: '2.7s', evidence: ['EVD-001'], reasoning: 'Isolation successful. Host-DX9 is now quarantined. No external communication possible.' },
  { id: 'SEED-4', type: 'THOUGHT',    agent: 'HERALD-03',   timestamp: '14:03:01.220', content: 'Lateral movement indicators detected. Evaluating blast radius. Checking adjacent subnet 192.168.1.0/24 for similar beaconing patterns.',                  entities: ['192.168.1.105'],                     mitre: 'T1021',     confidence: 78, tool: 'beacon_analyzer',  duration: '1.8s', evidence: ['EVD-003'], reasoning: 'IP beacon interval analysis shows 60s cadence matching APT-29 C2 profile in TI database (14 matches).' },
  { id: 'SEED-5', type: 'ACTION',     agent: 'HERALD-03',   timestamp: '14:03:04.090', content: null, code: 'enumerate_subnet --range 192.168.1.0/24 --depth 2',                   entities: ['192.168.1.105', 'Host-WS4'],         mitre: 'T1046',     confidence: 84, tool: 'network_scanner', duration: '0.5s', evidence: [],          reasoning: 'Enumerate the subnet to find any other hosts that may be beaconing to the same C2 server.', isPending: true },
];

// ── Timeline Component ────────────────────────────────────────────────
export default function AgentTimeline() {
  const { timelineEvents, entityFilter, clearEntityFilter } = useSOC();
  const [newIds, setNewIds] = useState(new Set());
  const prevLen = useRef(timelineEvents.length);
  const bottomRef = useRef(null);

  // Mark fresh events as "new" for animation
  useEffect(() => {
    if (timelineEvents.length > prevLen.current) {
      const freshs = timelineEvents.slice(prevLen.current).map(e => e.id);
      setNewIds(prev => new Set([...prev, ...freshs]));
      setTimeout(() => setNewIds(prev => {
        const next = new Set(prev);
        freshs.forEach(id => next.delete(id));
        return next;
      }), 1200);
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    prevLen.current = timelineEvents.length;
  }, [timelineEvents]);

  const allEvents = [...SEED_EVENTS, ...timelineEvents];

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-2">
          <Brain size={13} style={{ color: '#D84C7F' }} className="animate-pulse" />
          <span className="text-xs font-bold tracking-widest terminal" style={{ color: '#E2E8F0' }}>AGENT REASONING CHAIN</span>
        </div>
        <div className="flex items-center gap-3">
          {entityFilter && (
            <button onClick={clearEntityFilter}
              className="flex items-center gap-1 text-xs terminal px-2 py-0.5 rounded hover:brightness-125 transition-all"
              style={{ background: '#3B6FE318', color: '#3B6FE3', border: '1px solid #3B6FE333' }}>
              Filter: {entityFilter} ✕
            </button>
          )}
          <span className="text-xs terminal" style={{ color: '#6B7280' }}>
            {allEvents.length} STEPS
          </span>
          <span className="flex items-center gap-1.5 text-xs terminal" style={{ color: '#88C057' }}>
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-blink" />
            LIVE
          </span>
          <span className="text-xs terminal" style={{ color: '#D84C7F' }}>AUTONOMY LVL: HIGH</span>
        </div>
      </div>

      {/* Events */}
      <div className="flex-1 overflow-y-auto p-4 space-y-0">
        {allEvents.map((evt, i) => (
          <TimelineEntry key={evt.id} event={evt} isNew={newIds.has(evt.id)} />
        ))}

        {/* Live "processing" indicator */}
        <div className="pl-8 relative">
          <div className="absolute left-3 top-0 h-6 w-px" style={{ background: '#1F2937' }} />
          <div className="absolute left-1 top-2 w-5 h-5 rounded-full flex items-center justify-center"
            style={{ background: '#D84C7F22', border: '1.5px solid #D84C7F' }}>
            <div className="w-2 h-2 rounded-full bg-pink-500 animate-pulse" />
          </div>
          <div className="ml-2 text-xs terminal animate-pulse" style={{ color: '#D84C7F' }}>
            SENTINEL-01 PROCESSING...
          </div>
        </div>
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

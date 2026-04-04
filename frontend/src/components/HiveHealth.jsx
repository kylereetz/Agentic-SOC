import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Power, Activity, Cpu, Wifi, WifiOff, TrendingUp, Clock,
  AlertTriangle, Shield, ChevronRight, Zap, DollarSign, Layers, ShieldOff
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';
import AgentDetailDrawer from './AgentDetailDrawer';

// ── Agent Roster (synced with backend/soc/agents/ — 26 agents) ───────────────
const AGENT_ROSTER = [
  // Core Orchestration
  { id: 'SENTINEL-ORCHESTRATOR',      pillar: 'Core',      status: 'online',  load: 55, latency: 8,  task: 'Routing 6 pending alerts' },

  // Detection & Intelligence
  { id: 'SENTINEL-TRIAGE',            pillar: 'Intel',     status: 'online',  load: 92, latency: 22, task: 'Classifying 14 queued alerts' },
  { id: 'SENTINEL-CORRELATOR',        pillar: 'Intel',     status: 'online',  load: 61, latency: 15, task: 'Tracking campaign ALPHA-7' },
  { id: 'SENTINEL-LIBRARIAN',         pillar: 'Intel',     status: 'online',  load: 34, latency: 9,  task: 'Indexing 3 new case records' },
  { id: 'SENTINEL-HUNTER',            pillar: 'Intel',     status: 'online',  load: 88, latency: 35, task: 'APT29 hypothesis backtrack' },
  { id: 'SENTINEL-LOG-GUARDIAN',      pillar: 'Intel',     status: 'online',  load: 45, latency: 11, task: 'Normalizing Palo Alto logs' },
  { id: 'SENTINEL-TRAFFIC-SIEVE',     pillar: 'Intel',     status: 'online',  load: 72, latency: 18, task: 'Analyzing /24 netflow burst' },
  { id: 'SENTINEL-HISTORIAN',         pillar: 'Intel',     status: 'online',  load: 28, latency: 14, task: 'Archiving INC-2026-041 timeline' },

  // Response & Operations
  { id: 'SENTINEL-RESPONDER',         pillar: 'Response',  status: 'pending', load: 20, latency: 5,  task: 'Awaiting approval: VLAN block' },
  { id: 'SENTINEL-GATEKEEPER',        pillar: 'Response',  status: 'online',  load: 57, latency: 19, task: 'Rotating 3 NHI credentials' },
  { id: 'SENTINEL-VANGUARD',          pillar: 'Response',  status: 'online',  load: 30, latency: 13, task: 'Checking SBOM for CVE-2026-011' },
  { id: 'SENTINEL-MIRAGE',            pillar: 'Response',  status: 'online',  load: 5,  latency: 3,  task: 'Silent — 3 decoys active' },
  { id: 'SENTINEL-SCOUT',             pillar: 'Response',  status: 'online',  load: 22, latency: 21, task: 'Passive OT sweep subnet /16' },
  { id: 'SENTINEL-PATCH-PILOT',       pillar: 'Response',  status: 'idle',    load: 0,  latency: 0,  task: 'Awaiting VANGUARD risk handoff' },
  { id: 'SENTINEL-TOPOLOGY-MAPPER',   pillar: 'Response',  status: 'online',  load: 41, latency: 16, task: 'Building L3 graph for CORP-VLAN' },

  // Forensics & Analysis
  { id: 'SENTINEL-FORENSICS',         pillar: 'Forensics', status: 'online',  load: 77, latency: 28, task: 'Analyzing memdump HOST-DX9' },
  { id: 'SENTINEL-ENDPOINT-ANALYST',  pillar: 'Forensics', status: 'idle',    load: 0,  latency: 0,  task: 'Awaiting EDR telemetry pull' },
  { id: 'SENTINEL-MALWARE-PATHOLOGIST',pillar: 'Forensics', status: 'idle',   load: 0,  latency: 0,  task: 'Sandbox ready — no samples queued' },

  // Governance & Business
  { id: 'SENTINEL-GOVERNOR',          pillar: 'Gov',       status: 'online',  load: 25, latency: 8,  task: 'Cross-mapping NIST & CMMC controls' },
  { id: 'SENTINEL-COMMUNICATOR',      pillar: 'Gov',       status: 'online',  load: 12, latency: 10, task: 'Drafting board summary report' },
  { id: 'SENTINEL-WATCHDOG',          pillar: 'Gov',       status: 'online',  load: 8,  latency: 4,  task: 'Heartbeat polling all agents' },

  // Adversary Simulation
  { id: 'SENTINEL-RED-TEAM',          pillar: 'Sim',       status: 'idle',    load: 10, latency: 12, task: 'Awaiting Cyber Range parameters' },
];

const SPECIALIST_ROSTER = [
  { id: 'specialist-ot',    label: 'OT Security Analyst',    status: 'online', task: 'Modbus traffic analysis' },
  { id: 'specialist-net',   label: 'Net Behavior Analyst',   status: 'online', task: 'Baseline comparison' },
  { id: 'specialist-id',    label: 'Identity Access Analyst',status: 'online', task: 'IAM policy review' },
  { id: 'specialist-fix',   label: 'Remediation Analyst',    status: 'idle',   task: 'Awaiting assignment' },

  { id: 'specialist-lab',   label: 'Malware Pathologist',    status: 'idle',   task: 'Sandbox ready' },
  { id: 'specialist-hunt',  label: 'Threat Hunter',          status: 'online', task: 'Scanning for IOCs' },
];

const PILLAR_COLORS = {
  Core:      '#3B6FE3',
  Intel:     '#D84C7F',
  Response:  '#88C057',
  Forensics: '#E5A862',
  Gov:       '#A78BFA',
  Sim:       '#EF4444',
};

const STATUS_CFG = {
  online:  { color: '#88C057', label: 'ONLINE',  pulse: true },
  idle:    { color: '#4B5563', label: 'IDLE',    pulse: false },
  pending: { color: '#E5A862', label: 'PENDING', pulse: true },
  error:   { color: '#EF4444', label: 'ERROR',   pulse: true },
};

const WS_MESSAGES = [
  "ORCHESTRATOR >> routing ALRT-882 to SENTINEL-TRIAGE",
  "TRIAGE >> classified ALRT-882 as HIGH (Kerberoasting)",
  "ORCHESTRATOR >> case INC-2026-041 state OPEN → ACTIVE",
  "RED-TEAM >> deploying lateral movement payloads in Cyber Range",
  "CORRELATOR >> attachment: ALRT-882 → campaign ALPHA-7",
  "RESPONDER >> action queued: ISOLATE Switch-04 [PENDING HITL]",
  "HUNTER >> hypothesis APT29-MFG match: 4 historical events",
  "VANGUARD >> SBOM scan complete: 0 zero-days in batch",
  "MIRAGE >> silent monitoring — decoy PLC-SIEM-01 active",
  "WATCHDOG >> heartbeat OK — all 26 hive nodes responsive",
  "GATEKEEPER >> rotated API key for agent SENTINEL-HUNTER",
  "COMMUNICATOR >> board report draft #7 pushed to /reports",
  "GOVERNOR >> NIST 3.14.6 control verified against live topology",
  "GOVERNOR >> CMMC Level 3 compliance checks initiated",
  "HISTORIAN >> INC-2026-041 timeline archived to /cases/history",
  "FORENSICS >> Cobalt Strike shellcode confirmed: HOST-DX9 PID 9912",
  "TOPOLOGY-MAPPER >> L3 graph updated: 3 new nodes in CORP-VLAN",
  "PATCH-PILOT >> CVE-2026-011 assigned to VANGUARD for SBOM cross-check",
  "ENDPOINT-ANALYST >> EDR telemetry pull complete: 4 hosts",
  "MALWARE-PATHOLOGIST >> sandbox ready — detonation queue empty",
  "TRAFFIC-SIEVE >> exfiltration pattern detected: 192.168.1.105 → 203.0.113.45",
  "LOG-GUARDIAN >> 98.2% fast-path normalization on last batch (1,440 events)",
  "SCOUT >> OT discovery complete: 2 new PLCs on subnet 10.0.0.0/16",
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function AgentCard({ agent, onSelect }) {
  const st = STATUS_CFG[agent.status] || STATUS_CFG.idle;
  const pc = PILLAR_COLORS[agent.pillar] || '#6B7280';
  const loadColor = agent.load > 85 ? '#EF4444' : agent.load > 60 ? '#E5A862' : '#88C057';
  
  // Model Tiers for Multi-Head Architecture
  const modelTier = agent.id.includes('TRIAGE') || agent.id.includes('RESPONDER') || agent.id.includes('HUNTER') 
    ? { label: 'Reasoning', model: 'Llama 3.1 8B', color: '#D84C7F' }
    : { label: 'Fast',      model: 'Qwen 2.5 3B',  color: '#3B6FE3' };

  return (
    <div
      onClick={onSelect}
      className="rounded-lg p-3 transition-all hover:brightness-110 group cursor-pointer relative"
      style={{
        background: '#111827',
        border: `1px solid ${agent.status === 'online' ? pc + '33' : '#1F2937'}`,
      }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={`flex-shrink-0 w-2 h-2 rounded-full ${st.pulse ? 'animate-blink' : ''}`}
            style={{ background: st.color }}
          />
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-bold terminal truncate" style={{ color: pc }}>
              {agent.id.replace('SENTINEL-', 'S-')}
            </span>
            <span className="text-[9px] terminal opacity-50" style={{ color: modelTier.color }}>
              {modelTier.model}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end flex-shrink-0">
          <span className="text-[10px] font-bold terminal" style={{ color: '#4B5563' }}>
            {modelTier.label}
          </span>
          <span className="text-[9px] terminal" style={{ color: '#374151' }}>
            {agent.latency > 0 ? `${agent.latency}ms` : '—'}
          </span>
        </div>
      </div>

      {/* Load bar */}
      {agent.load > 0 && (
        <div className="h-1 rounded-full overflow-hidden mb-2" style={{ background: '#1F2937' }}>
          <div
            className="h-full rounded-full progress-bar"
            style={{ width: `${agent.load}%`, background: loadColor }}
          />
        </div>
      )}

      {/* Task */}
      <p className="h-meta mt-1 truncate">↳ {agent.task}</p>
    </div>
  );
}

function SpecialistCard({ specialist }) {
  const st = STATUS_CFG[specialist.status] || STATUS_CFG.idle;
  return (
    <div className="rounded-lg p-2 flex flex-col justify-between"
         style={{ background: '#111827', border: `1px solid ${st.color}33` }}>
      <div className="flex items-center gap-2 mb-1 min-w-0">
        <span className={`flex-shrink-0 w-2 h-2 rounded-full ${st.pulse ? 'animate-blink' : ''}`} style={{ background: st.color }} />
        <span className="text-[10px] font-bold terminal truncate" style={{ color: '#E2E8F0' }}>{specialist.label}</span>
      </div>
      <p className="text-[9px] truncate" style={{ color: '#6B7280' }}>↳ {specialist.task}</p>
    </div>
  );
}

function WSConsole({ lines }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [lines]);

  return (
    <div ref={ref} className="flex-1 overflow-y-auto font-mono text-xs p-3 space-y-1 scanline-overlay"
      style={{ background: '#080c12', color: '#4B5563' }}>
      {lines.map((line, i) => {
        const color = line.includes('PENDING') ? '#E5A862'
          : line.includes('>>') ? '#3B6FE380'
          : '#4B5563';
        const label = line.split('>>')[0]?.trim();
        const rest  = line.split('>>').slice(1).join('>>');
        return (
          <div key={i} className="flex gap-2 animate-slide-in-up" style={{ animationDelay: '0ms' }}>
            <span style={{ color: '#1F2937', flexShrink: 0 }}>
              {String(lines.length - i).padStart(4, '0')}
            </span>
            {rest ? (
              <>
                <span style={{ color: PILLAR_COLORS.Core }}>{label}</span>
                <span style={{ color: '#1F2937' }}>&gt;&gt;</span>
                <span style={{ color: '#9CA3AF' }}>{rest}</span>
              </>
            ) : (
              <span style={{ color: '#6B7280' }}>{line}</span>
            )}
          </div>
        );
      })}
      <span className="typing-cursor" style={{ color: '#3B6FE3' }} />
    </div>
  );
}

export default function HiveHealth() {
  const { user } = useAuth();
  const { autonomy, setAutonomy, killSwitch, toggleKillSwitch } = useSOC();
  const [agents, setAgents] = useState(AGENT_ROSTER);
  const [specialists, setSpecialists] = useState(SPECIALIST_ROSTER);
  const [wsLines, setWsLines] = useState(WS_MESSAGES.slice(0, 8));
  const [filter, setFilter] = useState('All');
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const msgIdx = useRef(8);

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    const id = setInterval(() => {
      setAgents(prev => prev.map(a => ({
        ...a,
        latency: a.status === 'idle' ? 0 : Math.max(3, a.latency + Math.round((Math.random() - 0.5) * 6)),
        load: a.status === 'idle' ? 0 : Math.min(99, Math.max(2, a.load + Math.round((Math.random() - 0.5) * 5))),
      })));

      setWsLines(prev => {
        const msg = WS_MESSAGES[msgIdx.current % WS_MESSAGES.length];
        msgIdx.current++;
        return [...prev.slice(-40), msg];
      });
    }, 2200);
    return () => clearInterval(id);
  }, []);

  const pillars = ['All', 'Core', 'Intel', 'Response', 'Forensics', 'Gov', 'Sim'];
  const visible = filter === 'All' ? agents : agents.filter(a => a.pillar === filter);

  const onlineCount  = agents.filter(a => a.status === 'online').length + specialists.filter(s => s.status === 'online').length;
  const totalNodes   = agents.length + specialists.length;
  const pendingCount = agents.filter(a => a.status === 'pending').length;
  const avgLatency   = Math.round(agents.filter(a => a.latency > 0).reduce((s, a) => s + a.latency, 0) / agents.filter(a => a.latency > 0).length);



  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <Activity size={14} style={{ color: '#88C057' }} className="animate-pulse" />
          <span className="panel-heading">Global Hive Health</span>
          <span className="h-meta px-2 py-0.5 rounded-full"
            style={{ background: '#88C05720', color: '#88C057', border: '1px solid #88C05733' }}>
            {onlineCount}/{totalNodes} ONLINE
          </span>
        </div>

        {/* Kill Switch — reads from SOCContext, synced with Header */}
        <button
          onClick={toggleKillSwitch}
          disabled={!isAdmin}
          className={`flex items-center gap-2 text-xs terminal px-4 py-2 rounded-lg font-bold transition-all ${
            !isAdmin ? 'opacity-50 cursor-not-allowed' : 'action-btn ' + (!killSwitch ? 'kill-switch-pulse' : '')
          }`}
          style={{
            background: killSwitch ? '#EF44441A' : '#EF444422',
            color: killSwitch ? '#EF4444' : '#EF4444',
            border: `1px solid ${killSwitch ? '#EF4444' : '#EF444466'}`,
            boxShadow: killSwitch ? '0 0 16px rgba(239,68,68,0.4)' : 'none',
          }}>
          {isAdmin ? <Power size={13} className={killSwitch ? 'animate-pulse' : ''} /> : <Shield size={13} style={{ color: '#D84C7F' }} />}
          {killSwitch ? '⚠ KILL SWITCH ACTIVE' : isAdmin ? '⚡ GLOBAL KILL SWITCH' : 'KILL SWITCH (LOCKED)'}
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-3 px-5 py-3 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
        {[
          { icon: Activity,     val: `${onlineCount}/${totalNodes}`, label: 'Nodes Online',    color: '#88C057' },
          { icon: Cpu,          val: `Ollama Local`,                 label: 'Inference Engine', color: '#D84C7F' },
          { icon: Clock,        val: `${avgLatency}ms`,              label: 'Avg Latency',      color: '#3B6FE3' },
          { icon: AlertTriangle,val: `${pendingCount}`,              label: 'HITL Pending',     color: '#E5A862' },
        ].map(({ icon: Icon, val, label, color }) => (
          <div key={label} className="kpi-card flex items-center gap-3">
            <Icon size={20} style={{ color, flexShrink: 0 }} />
            <div>
              <p className="h-stat-sm" style={{ color }}>{val}</p>
              <p className="h-label mt-0.5">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* LEFT: Agent Matrix */}
        <div className="flex flex-col" style={{ flex: '0 0 58%', minWidth: 380, borderRight: '1px solid #1F2937' }}>
          {/* Pillar filter */}
          <div className="flex items-center gap-1.5 px-4 py-2 border-b flex-shrink-0"
            style={{ borderColor: '#1F2937' }}>
            {pillars.map(p => (
              <button key={p} onClick={() => setFilter(p)}
                className="text-xs terminal px-2.5 py-1 rounded transition-all"
                style={{
                  background: filter === p ? (PILLAR_COLORS[p] || '#FFFFFF') + '22' : 'transparent',
                  color: filter === p ? (PILLAR_COLORS[p] || '#E2E8F0') : '#4B5563',
                  border: `1px solid ${filter === p ? (PILLAR_COLORS[p] || '#6B7280') + '44' : 'transparent'}`,
                }}>
                {p}
              </button>
            ))}
          </div>

          {/* Grid */}
          <div className="flex-1 overflow-y-auto p-4 grid gap-2"
            style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', alignContent: 'start' }}>
            {visible.length === 0 ? (
              <div className="col-span-full flex flex-col items-center justify-center p-12 opacity-50 space-y-3">
                <ShieldOff size={32} color="#6B7280" />
                <p className="h-body text-[#6B7280]">No sentinels match current pillar filter.</p>
              </div>
            ) : visible.map(a => <AgentCard key={a.id} agent={a} onSelect={() => setSelectedAgentId(a.id)} />)}
          </div>
        </div>

        {/* RIGHT: Auxiliary Nodes + Autonomy + Console */}
        <div className="flex flex-col flex-1 min-w-0">
          
          {/* Secondary Sentinels (Specialists) */}
          <div className="px-4 py-4 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
            <div className="flex items-center gap-2 mb-3">
              <Layers size={12} style={{ color: '#3B6FE3' }} />
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>SPECIALIST WORKER NODES</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {specialists.map(s => <SpecialistCard key={s.id} specialist={s} />)}
            </div>
          </div>

          {/* Hive Learning (MARL) Insights */}
          <div className="px-4 py-4 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <TrendingUp size={12} style={{ color: '#88C057' }} />
                <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>HIVE LEARNING (MARL)</span>
              </div>
              <span className="text-[10px] terminal uppercase" style={{ color: '#4B5563' }}>Q-Table Convergence: 82%</span>
            </div>
            
            <div className="space-y-3">
              {[
                { label: 'Triage Accuracy', reward: +0.12, q: 0.88, color: '#D84C7F' },
                { label: 'Response Efficiency', reward: +0.05, q: 0.74, color: '#3B6FE3' },
                { label: 'False Positive Aversion', reward: -0.02, q: 0.91, color: '#88C057' },
              ].map(stat => (
                <div key={stat.label} className="space-y-1">
                  <div className="flex justify-between text-[10px] terminal">
                    <span style={{ color: '#9CA3AF' }}>{stat.label}</span>
                    <span style={{ color: stat.reward >= 0 ? '#88C057' : '#EF4444' }}>
                      {stat.reward >= 0 ? '+' : ''}{stat.reward} RWD
                    </span>
                  </div>
                  <div className="h-1 rounded-full overflow-hidden flex gap-0.5" style={{ background: '#1F2937' }}>
                    <div className="h-full rounded-full transition-all duration-700" 
                      style={{ width: `${stat.q * 100}%`, background: stat.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Autonomy Slider */}
          <div className="px-4 py-4 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Shield size={12} style={{ color: '#D84C7F' }} />
                <span className="text-xs terminal" style={{ color: '#6B7280' }}>SYSTEM AUTONOMY LEVEL</span>
              </div>
              <span className="text-sm font-bold terminal" style={{ color: '#D84C7F' }}>
                {autonomy?.level ?? 75}% {!isAdmin && ' (LOCKED)'}
              </span>
            </div>
            <input type="range" min={0} max={100} value={autonomy?.level ?? 75}
              disabled={!isAdmin}
              onChange={e => isAdmin && setAutonomy && setAutonomy(v => ({ ...v, level: +e.target.value }))}
              className={`w-full h-1.5 rounded-full appearance-none ${isAdmin ? 'cursor-pointer' : 'cursor-not-allowed'}`}
              style={{ accentColor: '#D84C7F', background: `linear-gradient(to right, #D84C7F ${autonomy?.level ?? 75}%, #1F2937 ${autonomy?.level ?? 75}%)` }}
            />
            <div className="flex justify-between text-xs terminal mt-1.5" style={{ color: '#374151' }}>
              <span>Manual</span>
              <span>Semi-Auto</span>
              <span>Full-Auto</span>
            </div>
          </div>

          {/* WebSocket Console */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex items-center gap-2 px-4 py-2 flex-shrink-0 border-b" style={{ borderColor: '#1F2937' }}>
              <Wifi size={11} style={{ color: '#88C057' }} className="animate-blink" />
              <span className="text-xs terminal" style={{ color: '#4B5563' }}>ORCHESTRATOR EVENT STREAM</span>
            </div>
            <WSConsole lines={wsLines} />
          </div>
        </div>
      </div>
      
      <AgentDetailDrawer 
        agentId={selectedAgentId} 
        onClose={() => setSelectedAgentId(null)} 
      />
    </div>
  );
}

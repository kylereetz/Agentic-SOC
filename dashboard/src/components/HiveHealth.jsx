import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Power, Activity, Cpu, Wifi, WifiOff, TrendingUp, Clock,
  AlertTriangle, Shield, ChevronRight, Zap, DollarSign, Layers
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

// ── Mock Data ─────────────────────────────────────────────────────────────────
const AGENT_ROSTER = [
  // Core Orchestration
  { id: 'SENTINEL-MANAGER',    pillar: 'Core',     status: 'online',  load: 78, latency: 12, task: 'Managing case INC-2026-041' },
  { id: 'SENTINEL-ORCHESTRATOR',pillar: 'Core',    status: 'online',  load: 55, latency: 8,  task: 'Routing 6 pending alerts' },
  // Detection & Intelligence
  { id: 'SENTINEL-TRIAGE',     pillar: 'Intel',    status: 'online',  load: 92, latency: 22, task: 'Classifying 14 queued alerts' },
  { id: 'SENTINEL-CORRELATOR', pillar: 'Intel',    status: 'online',  load: 61, latency: 15, task: 'Tracking campaign ALPHA-7' },
  { id: 'SENTINEL-LIBRARIAN',  pillar: 'Intel',    status: 'online',  load: 34, latency: 9,  task: 'Indexing 3 new case records' },
  { id: 'SENTINEL-HUNTER',     pillar: 'Intel',    status: 'online',  load: 88, latency: 35, task: 'APT29 hypothesis backtrack' },
  { id: 'SENTINEL-LOG-GUARDIAN',pillar: 'Intel',   status: 'online',  load: 45, latency: 11, task: 'Normalizing Palo Alto logs' },
  { id: 'SENTINEL-TRAFFIC-SIEVE',pillar:'Intel',   status: 'online',  load: 72, latency: 18, task: 'Analyzing /24 netflow burst' },
  // Investigation & Engineering
  { id: 'SENTINEL-INVESTIGATOR',pillar: 'Invest',  status: 'online',  load: 95, latency: 180, task: 'CoT reasoning on ALT-004' },
  { id: 'SENTINEL-FORENSICS',  pillar: 'Invest',   status: 'online',  load: 67, latency: 42, task: 'Processing HOST-DX9 memdump' },
  { id: 'SENTINEL-MALWARE-PATH',pillar: 'Invest',  status: 'idle',    load: 0,  latency: 0,  task: 'Idle — awaiting sample' },
  { id: 'SENTINEL-CLOUD-WRAITH',pillar: 'Invest',  status: 'online',  load: 38, latency: 29, task: 'Watching AWS CloudTrail' },
  // Response & Operations
  { id: 'SENTINEL-RESPONDER',  pillar: 'Response', status: 'pending', load: 20, latency: 5,  task: 'Awaiting approval: VLAN block' },
  { id: 'SENTINEL-DISPATCH',   pillar: 'Response', status: 'online',  load: 15, latency: 7,  task: 'Sent PagerDuty alert #1882' },
  { id: 'SENTINEL-PATCHPILOT', pillar: 'Response', status: 'online',  load: 41, latency: 14, task: 'Scheduling log4j patch wks-04' },
  { id: 'SENTINEL-GATEKEEPER', pillar: 'Response', status: 'online',  load: 57, latency: 19, task: 'Rotating 3 NHI credentials' },
  { id: 'SENTINEL-VANGUARD',   pillar: 'Response', status: 'online',  load: 30, latency: 13, task: 'Checking SBOM for CVE-2026-011' },
  { id: 'SENTINEL-MIRAGE',     pillar: 'Response', status: 'online',  load: 5,  latency: 3,  task: 'Silent — 3 decoys active' },
  { id: 'SENTINEL-SCOUT',      pillar: 'Response', status: 'online',  load: 22, latency: 21, task: 'Passive OT sweep subnet /16' },
  // Business & Governance
  { id: 'SENTINEL-AUDITOR',    pillar: 'Gov',      status: 'online',  load: 18, latency: 6,  task: 'NIST control audit cycle' },
  { id: 'SENTINEL-RISK-QUANT', pillar: 'Gov',      status: 'online',  load: 25, latency: 8,  task: 'Loss magnitude calculations' },
  { id: 'SENTINEL-POLICY-ARCH',pillar: 'Gov',      status: 'idle',    load: 0,  latency: 0,  task: 'Idle — awaiting feedback batch' },
  { id: 'SENTINEL-NARRATOR',   pillar: 'Gov',      status: 'online',  load: 12, latency: 10, task: 'Drafting board summary #7' },
  { id: 'SENTINEL-WATCHDOG',   pillar: 'Gov',      status: 'online',  load: 8,  latency: 4,  task: 'Heartbeat polling all 24 agents' },
];

const PILLAR_COLORS = {
  Core:     '#3B6FE3',
  Intel:    '#D84C7F',
  Invest:   '#E5A862',
  Response: '#88C057',
  Gov:      '#A78BFA',
};

const STATUS_CFG = {
  online:  { color: '#88C057', label: 'ONLINE',  pulse: true },
  idle:    { color: '#4B5563', label: 'IDLE',    pulse: false },
  pending: { color: '#E5A862', label: 'PENDING', pulse: true },
  error:   { color: '#EF4444', label: 'ERROR',   pulse: true },
};

// Generate rolling mock telemetry
function makeTelemetryPoints(n = 20) {
  return Array.from({ length: n }, (_, i) => ({
    t: i,
    tokens: 5000 + Math.random() * 12000,
    cost: 0.02 + Math.random() * 0.18,
  }));
}

const WS_MESSAGES = [
  "ORCHESTRATOR >> routing ALRT-882 to SENTINEL-TRIAGE",
  "TRIAGE >> classified ALRT-882 as HIGH (Kerberoasting)",
  "MANAGER >> case INC-2026-041 state OPEN → ACTIVE",
  "INVESTIGATOR >> starting CoT reasoning on ALRT-882",
  "FORENSICS >> evidence collection requested: HOST-DX9",
  "CORRELATOR >> attachment: ALRT-882 → campaign ALPHA-7",
  "RESPONDER >> action queued: ISOLATE Switch-04 [PENDING HITL]",
  "HUNTER >> hypothesis APT29-MFG match: 4 historical events",
  "VANGUARD >> SBOM scan complete: 0 zero-days in batch",
  "MIRAGE >> silent monitoring — decoy PLC-SIEM-01 active",
  "WATCHDOG >> heartbeat OK — all 24 agents responsive",
  "GATEKEEPER >> rotated API key for agent SENTINEL-HUNTER",
  "NARRATOR >> board report draft #7 pushed to /reports",
  "AUDITOR >> NIST 3.14.6 control last verified 00:12:03 ago",
  "RISK-QUANT >> INC-2026-041 loss magnitude: $88,400/hr",
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function AgentCard({ agent, tokensMap }) {
  const st = STATUS_CFG[agent.status] || STATUS_CFG.idle;
  const pc = PILLAR_COLORS[agent.pillar] || '#6B7280';
  const loadColor = agent.load > 85 ? '#EF4444' : agent.load > 60 ? '#E5A862' : '#88C057';

  return (
    <div
      className="rounded-lg p-3 transition-all hover:brightness-110 group cursor-default"
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
          <span className="text-xs font-bold terminal truncate" style={{ color: pc }}>
            {agent.id.replace('SENTINEL-', 'S-')}
          </span>
        </div>
        <span className="text-xs terminal flex-shrink-0" style={{ color: '#4B5563' }}>
          {agent.latency > 0 ? `${agent.latency}ms` : '—'}
        </span>
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
      <p className="text-xs italic truncate" style={{ color: '#6B7280' }}>
        ↳ {agent.task}
      </p>
    </div>
  );
}

function TelemetryChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={110}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -30 }}>
        <defs>
          <linearGradient id="tokGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#3B6FE3" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#3B6FE3" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#D84C7F" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#D84C7F" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
        <XAxis dataKey="t" hide />
        <YAxis tick={{ fill: '#4B5563', fontSize: 9 }} />
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #1F2937', borderRadius: 6, fontSize: 11 }}
          labelStyle={{ color: '#6B7280' }}
          formatter={(v, n) => [n === 'tokens' ? `${Math.round(v).toLocaleString()} tok` : `$${v.toFixed(3)}`, n]}
        />
        <Area type="monotone" dataKey="tokens" stroke="#3B6FE3" strokeWidth={1.5} fill="url(#tokGrad)" dot={false} />
        <Area type="monotone" dataKey="cost"   stroke="#D84C7F" strokeWidth={1.5} fill="url(#costGrad)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
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

// ── Main Component ─────────────────────────────────────────────────────────────
export default function HiveHealth() {
  const { user } = useAuth();
  const { autonomy, setAutonomy } = useSOC();
  const [agents, setAgents] = useState(AGENT_ROSTER);
  const [telemetry, setTelemetry] = useState(makeTelemetryPoints());
  const [wsLines, setWsLines] = useState(WS_MESSAGES.slice(0, 8));
  const [killed, setKilled] = useState(false);
  const [filter, setFilter] = useState('All');
  const msgIdx = useRef(8);

  const isAdmin = user?.role === 'admin';

  // Tick: update latencies + append WS messages
  useEffect(() => {
    const id = setInterval(() => {
      setAgents(prev => prev.map(a => ({
        ...a,
        latency: a.status === 'idle' ? 0 : Math.max(3, a.latency + Math.round((Math.random() - 0.5) * 6)),
        load: a.status === 'idle' ? 0 : Math.min(99, Math.max(2, a.load + Math.round((Math.random() - 0.5) * 5))),
      })));

      setTelemetry(prev => {
        const next = [...prev.slice(1), { t: prev[prev.length - 1].t + 1, tokens: 5000 + Math.random() * 12000, cost: 0.02 + Math.random() * 0.18 }];
        return next;
      });

      setWsLines(prev => {
        const msg = WS_MESSAGES[msgIdx.current % WS_MESSAGES.length];
        msgIdx.current++;
        return [...prev.slice(-40), msg];
      });
    }, 2200);
    return () => clearInterval(id);
  }, []);

  const pillars = ['All', 'Core', 'Intel', 'Invest', 'Response', 'Gov'];
  const visible = filter === 'All' ? agents : agents.filter(a => a.pillar === filter);

  const onlineCount  = agents.filter(a => a.status === 'online').length;
  const pendingCount = agents.filter(a => a.status === 'pending').length;
  const avgLatency   = Math.round(agents.filter(a => a.latency > 0).reduce((s, a) => s + a.latency, 0) / agents.filter(a => a.latency > 0).length);
  const totalTokens  = Math.round(telemetry.reduce((s, p) => s + p.tokens, 0) / telemetry.length);

  const handleKill = useCallback(() => {
    if (!isAdmin) return;
    setKilled(v => !v);
  }, [isAdmin]);

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <Activity size={14} style={{ color: '#88C057' }} className="animate-pulse" />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            GLOBAL HIVE HEALTH
          </span>
          <span className="terminal text-xs px-2 py-0.5 rounded-full"
            style={{ background: '#88C05720', color: '#88C057', border: '1px solid #88C05733' }}>
            {onlineCount}/{agents.length} ONLINE
          </span>
        </div>

        {/* Kill Switch */}
        <button
          onClick={handleKill}
          disabled={!isAdmin}
          className={`flex items-center gap-2 text-xs terminal px-4 py-2 rounded-lg font-bold transition-all ${
            !isAdmin ? 'opacity-50 cursor-not-allowed' : 'action-btn ' + (!killed ? 'kill-switch-pulse' : '')
          }`}
          style={{
            background: killed ? '#1F2937' : '#EF444422',
            color: killed ? '#6B7280' : '#EF4444',
            border: `1px solid ${killed ? '#374151' : '#EF444466'}`,
          }}>
          {isAdmin ? <Power size={13} /> : <Shield size={13} style={{ color: '#D84C7F' }} />}
          {killed ? 'RESPONDER: PAUSED' : isAdmin ? '⚡ GLOBAL KILL SWITCH' : 'KILL SWITCH (LOCKED)'}
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-3 px-5 py-3 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
        {[
          { icon: Activity,   val: `${onlineCount}/24`, label: 'Agents Online',   color: '#88C057' },
          { icon: Clock,      val: `${avgLatency}ms`,    label: 'Avg Latency',     color: '#3B6FE3' },
          { icon: AlertTriangle,val:`${pendingCount}`,   label: 'HITL Pending',    color: '#E5A862' },
          { icon: DollarSign, val: `$${(telemetry[telemetry.length-1]?.cost || 0.07).toFixed(3)}/s`, label: 'API Cost Rate', color: '#D84C7F' },
        ].map(({ icon: Icon, val, label, color }) => (
          <div key={label} className="flex items-center gap-3 rounded-lg px-4 py-3"
            style={{ background: '#111827', border: '1px solid #1F2937' }}>
            <Icon size={18} style={{ color, flexShrink: 0 }} />
            <div>
              <p className="text-sm font-bold" style={{ color }}>{val}</p>
              <p className="text-xs terminal" style={{ color: '#6B7280' }}>{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* LEFT: Agent Matrix */}
        <div className="flex flex-col" style={{ width: '58%', borderRight: '1px solid #1F2937' }}>
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
            {visible.map(a => <AgentCard key={a.id} agent={a} />)}
          </div>
        </div>

        {/* RIGHT: Telemetry + Autonomy + Console */}
        <div className="flex flex-col flex-1 min-w-0">
          {/* Telemetry chart */}
          <div className="px-4 pt-4 pb-2 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <TrendingUp size={12} style={{ color: '#3B6FE3' }} />
                <span className="text-xs terminal" style={{ color: '#6B7280' }}>LLM TOKEN BURN / API COST</span>
              </div>
              <div className="flex items-center gap-3 text-xs terminal">
                <span style={{ color: '#3B6FE3' }}>● Tokens</span>
                <span style={{ color: '#D84C7F' }}>● Cost ($)</span>
              </div>
            </div>
            <TelemetryChart data={telemetry} />
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
    </div>
  );
}

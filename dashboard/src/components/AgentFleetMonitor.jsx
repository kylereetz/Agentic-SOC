import React, { useState, useEffect } from 'react';
import { Bot, CheckCircle, Clock, Zap, TrendingUp, AlertCircle, Pause } from 'lucide-react';
import AgentDetailDrawer from './AgentDetailDrawer';

const AGENT_DEFS = [
  { id: 'MANAGER-01',       role: 'InvestigationManager',   color: '#3B6FE3', status: 'ACTIVE',  task: 'Orchestrating Case INC-2023-981', runtime: '12:44', success: 99, tools: 142 },
  { id: 'ORCHESTRATOR-01',  role: 'Orchestrator',           color: '#D84C7F', status: 'ACTIVE',  task: 'Dispatching tasks for INC-2023-981', runtime: '12:44', success: 98, tools: 88 },
  { id: 'TRIAGE-01',        role: 'TriageAgent',            color: '#3B6FE3', status: 'ACTIVE',  task: 'Classifying incoming EventBus anomalies', runtime: '48:12', success: 92, tools: 1050 },
  { id: 'CORRELATOR-01',    role: 'CorrelatorAgent',        color: '#E5A862', status: 'IDLE',    task: 'Awaiting new historical linkages', runtime: '00:00', success: 94, tools: 12 },
  { id: 'LIBRARIAN-01',     role: 'LibrarianAgent',         color: '#88C057', status: 'ACTIVE',  task: 'Indexing resolved case data to Vector DB', runtime: '04:12', success: 100, tools: 45 },
  { id: 'HUNTER-01',        role: 'HunterAgent',            color: '#D84C7F', status: 'ACTIVE',  task: 'Executing hypothesis-driven threat hunt', runtime: '14:22', success: 87, tools: 67 },
  { id: 'LOG-GUARDIAN-01',  role: 'LogGuardianAgent',       color: '#3B6FE3', status: 'ACTIVE',  task: 'Normalizing proprietary CEF logs', runtime: '55:10', success: 99, tools: 210 },
  { id: 'TRAFFIC-SIEVE-01', role: 'TrafficSieveAgent',      color: '#88C057', status: 'ACTIVE',  task: 'Analyzing netflow for data exfiltration', runtime: '22:15', success: 91, tools: 154 },
  { id: 'ENDPT-ANALYST-01', role: 'EndpointAnalystAgent',   color: '#3B6FE3', status: 'ACTIVE',  task: 'Parsing Sysmon EDR telemetry', runtime: '11:05', success: 96, tools: 88 },
  { id: 'INVESTIGATOR-01',  role: 'InvestigatorAgent',      color: '#D84C7F', status: 'ACTIVE',  task: 'Performing CoT reasoning on Host-DX9', runtime: '08:44', success: 93, tools: 56 },
  { id: 'FORENSICS-01',     role: 'ForensicsAgent',         color: '#88C057', status: 'IDLE',    task: 'Awaiting memory dump acquisition orders', runtime: '00:00', success: 88, tools: 0 },
  { id: 'PATHOLOGIST-01',   role: 'MalwarePathologistAgent',color: '#EF4444', status: 'IDLE',    task: 'Awaiting binary extraction for sandbox analysis', runtime: '00:00', success: 95, tools: 0 },
  { id: 'CLOUD-WRAITH-01',  role: 'CloudWraithAgent',       color: '#3B6FE3', status: 'ACTIVE',  task: 'Monitoring AWS IAM CloudTrail anomalies', runtime: '19:30', success: 98, tools: 112 },
  { id: 'RESPONDER-01',     role: 'ResponderAgent',         color: '#EF4444', status: 'WAITING', task: 'Waiting for analyst approval — block_firewall', runtime: '02:11', success: 100, tools: 5 },
  { id: 'PATCHPILOT-01',    role: 'PatchPilot',             color: '#88C057', status: 'IDLE',    task: 'Awaiting remediation vulnerability assignments', runtime: '00:00', success: 99, tools: 0 },
  { id: 'GATEKEEPER-01',    role: 'GatekeeperAgent',        color: '#E5A862', status: 'ACTIVE',  task: 'Auditing impossible travel ID anomalies', runtime: '33:10', success: 95, tools: 201 },
  { id: 'VANGUARD-01',      role: 'VanguardAgent',          color: '#3B6FE3', status: 'IDLE',    task: 'Awaiting SBOM composition updates', runtime: '00:00', success: 100, tools: 0 },
  { id: 'MIRAGE-01',        role: 'MirageAgent',            color: '#D84C7F', status: 'ACTIVE',  task: 'Monitoring deception honeypot beacons', runtime: '100:10', success: 100, tools: 50 },
  { id: 'SCOUT-01',         role: 'ScoutAgent',             color: '#88C057', status: 'ACTIVE',  task: 'Passive network discovery on subnet /24', runtime: '41:15', success: 90, tools: 334 },
  { id: 'GOVERNOR-01',      role: 'GovernorAgent',          color: '#E5A862', status: 'IDLE',    task: 'Awaiting compliance cross-mapping requests', runtime: '00:00', success: 98, tools: 0 },
  { id: 'COMMUNICATOR-01',  role: 'CommunicatorAgent',      color: '#3B6FE3', status: 'ACTIVE',  task: 'Synthesizing executive report for INC-2023-981', runtime: '01:22', success: 99, tools: 4 },
  { id: 'WATCHDOG-01',      role: 'WatchdogAgent',          color: '#EF4444', status: 'ACTIVE',  task: 'Monitoring hive telemetry health & latency', runtime: '124:00', success: 100, tools: 888 },
];

const STATUS_STYLE = {
  ACTIVE:   { color: '#88C057', bg: '#88C05720', label: 'ACTIVE', pulse: true },
  WAITING:  { color: '#E5A862', bg: '#E5A86220', label: 'WAITING APPROVAL', pulse: false },
  IDLE:     { color: '#4B5563', bg: '#FFFFFF08', label: 'IDLE', pulse: false },
};

function SuccessBar({ value, color }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ background: '#1F2937' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-xs terminal" style={{ color, minWidth: 28 }}>{value}%</span>
    </div>
  );
}

export default function AgentFleetMonitor() {
  const [agents, setAgents] = useState(AGENT_DEFS);
  const [tick, setTick] = useState(0);
  const [selectedAgentId, setSelectedAgentId] = useState(null);

  // Simulate tool count ticking for active agents
  useEffect(() => {
    const id = setInterval(() => {
      setTick(t => t + 1);
      setAgents(prev => prev.map(a =>
        a.status === 'ACTIVE' && Math.random() > 0.7
          ? { ...a, tools: a.tools + 1 }
          : a
      ));
    }, 2000);
    return () => clearInterval(id);
  }, []);

  const active = agents.filter(a => a.status === 'ACTIVE').length;

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-2">
          <Bot size={14} style={{ color: '#D84C7F' }} className="animate-pulse" />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>AGENT FLEET MONITOR</span>
        </div>
        <div className="flex items-center gap-4 terminal text-xs" style={{ color: '#6B7280' }}>
          <span style={{ color: '#88C057' }}>{active} ACTIVE</span>
          <span>/ {agents.length} TOTAL</span>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-2 p-4 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
        {[
          { label: 'Active Agents', value: `${active}/${agents.length}`, color: '#88C057' },
          { label: 'Tools Executed', value: agents.reduce((s, a) => s + a.tools, 0), color: '#3B6FE3' },
          { label: 'Avg. Success', value: `${Math.round(agents.reduce((s, a) => s + a.success, 0) / agents.length)}%`, color: '#D84C7F' },
          { label: 'Human Approvals', value: '3 pending', color: '#E5A862' },
        ].map(({ label, value, color }) => (
          <div key={label} className="rounded-lg p-3" style={{ background: '#111827', border: '1px solid #1F2937' }}>
            <p className="text-xs terminal" style={{ color: '#6B7280' }}>{label}</p>
            <p className="text-sm font-bold mt-1" style={{ color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Agent Cards */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {agents.map(agent => {
          const st = STATUS_STYLE[agent.status];
          return (
            <div key={agent.id} 
              className="rounded-lg p-4 transition-all hover:brightness-110 cursor-pointer"
              onClick={() => setSelectedAgentId(agent.id)}
              style={{ background: '#111827', border: `1px solid ${agent.status === 'ACTIVE' ? agent.color + '33' : '#1F2937'}` }}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full flex items-center justify-center"
                    style={{ background: agent.color + '22', border: `1px solid ${agent.color}` }}>
                    <Bot size={16} style={{ color: agent.color }} />
                  </div>
                  <div>
                    <p className="text-sm font-bold" style={{ color: agent.color }}>{agent.id}</p>
                    <p className="text-xs terminal" style={{ color: '#6B7280' }}>{agent.role}</p>
                  </div>
                </div>
                <span className="flex items-center gap-1.5 text-xs terminal px-2 py-1 rounded-full"
                  style={{ background: st.bg, color: st.color, border: `1px solid ${st.color}33` }}>
                  <span className={`w-1.5 h-1.5 rounded-full ${st.pulse ? 'animate-blink' : ''}`} style={{ background: st.color }} />
                  {st.label}
                </span>
              </div>

              <p className="text-xs mb-3 italic" style={{ color: '#9CA3AF' }}>↳ {agent.task}</p>

              <div className="grid grid-cols-3 gap-3 text-xs terminal">
                <div>
                  <p style={{ color: '#6B7280' }}>Runtime</p>
                  <div className="flex items-center gap-1 mt-1">
                    <Clock size={11} style={{ color: '#6B7280' }} />
                    <span style={{ color: '#CBD5E1' }}>{agent.runtime}</span>
                  </div>
                </div>
                <div>
                  <p style={{ color: '#6B7280' }}>Tools Used</p>
                  <div className="flex items-center gap-1 mt-1">
                    <Zap size={11} style={{ color: '#3B6FE3' }} />
                    <span style={{ color: '#93C5FD' }}>{agent.tools}</span>
                  </div>
                </div>
                <div>
                  <p style={{ color: '#6B7280' }}>Success Rate</p>
                  <div className="mt-1">
                    <SuccessBar value={agent.success} color={agent.color} />
                  </div>
                </div>
              </div>

              {agent.status === 'WAITING' && (
                <div className="flex gap-2 mt-3">
                  <button className="flex-1 text-xs terminal py-1.5 rounded hover:brightness-125 transition-all"
                    style={{ background: '#88C05720', color: '#88C057', border: '1px solid #88C05733' }}>
                    ✓ Approve Action
                  </button>
                  <button className="flex-1 text-xs terminal py-1.5 rounded hover:brightness-125 transition-all"
                    style={{ background: '#EF444420', color: '#EF4444', border: '1px solid #EF444433' }}>
                    ✕ Reject
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <AgentDetailDrawer 
        agentId={selectedAgentId} 
        onClose={() => setSelectedAgentId(null)} 
      />
    </div>
  );
}

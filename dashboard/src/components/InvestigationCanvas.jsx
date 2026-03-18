import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap,
  useNodesState, useEdgesState, addEdge, MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ChevronDown, ChevronRight, Clock, Check, X, ShieldAlert, GitBranch, User, Lock } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

// ── Mock Data ─────────────────────────────────────────────────────────────────
const INITIAL_NODES = [
  {
    id: '1', type: 'default', position: { x: 60, y: 180 },
    data: { label: '🔍 RECON\nHost-DX9 Sweep' },
    style: { background: '#D84C7F22', border: '1px solid #D84C7F', color: '#D84C7F', borderRadius: 8, padding: '10px 16px', fontSize: 11, fontFamily: 'JetBrains Mono', width: 150, whiteSpace: 'pre-line', textAlign: 'center' },
  },
  {
    id: '2', type: 'default', position: { x: 270, y: 100 },
    data: { label: '↔ PIVOT\nSMB → DC-01' },
    style: { background: '#E5A86222', border: '1px solid #E5A862', color: '#E5A862', borderRadius: 8, padding: '10px 16px', fontSize: 11, fontFamily: 'JetBrains Mono', width: 150, whiteSpace: 'pre-line', textAlign: 'center' },
  },
  {
    id: '3', type: 'default', position: { x: 270, y: 270 },
    data: { label: '🔑 CREDENTIAL\nKerberoasting' },
    style: { background: '#EF444422', border: '1px solid #EF4444', color: '#EF4444', borderRadius: 8, padding: '10px 16px', fontSize: 11, fontFamily: 'JetBrains Mono', width: 150, whiteSpace: 'pre-line', textAlign: 'center' },
  },
  {
    id: '4', type: 'default', position: { x: 490, y: 180 },
    data: { label: '🪝 PERSIST\nRegistry Run Key' },
    style: { background: '#A78BFA22', border: '1px solid #A78BFA', color: '#A78BFA', borderRadius: 8, padding: '10px 16px', fontSize: 11, fontFamily: 'JetBrains Mono', width: 150, whiteSpace: 'pre-line', textAlign: 'center' },
  },
  {
    id: '5', type: 'default', position: { x: 710, y: 100 },
    data: { label: '📤 EXFIL\n2.1MB to C2' },
    style: { background: '#3B6FE322', border: '1px solid #3B6FE3', color: '#3B6FE3', borderRadius: 8, padding: '10px 16px', fontSize: 11, fontFamily: 'JetBrains Mono', width: 150, whiteSpace: 'pre-line', textAlign: 'center' },
  },
  {
    id: '6', type: 'default', position: { x: 710, y: 270 },
    data: { label: '📡 C2\n45.33.22.11:443' },
    style: { background: '#88C05722', border: '1px solid #88C057', color: '#88C057', borderRadius: 8, padding: '10px 16px', fontSize: 11, fontFamily: 'JetBrains Mono', width: 150, whiteSpace: 'pre-line', textAlign: 'center' },
  },
];

const INITIAL_EDGES = [
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#E5A862', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#E5A862' } },
  { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#EF4444', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#EF4444' } },
  { id: 'e2-4', source: '2', target: '4', animated: true, style: { stroke: '#A78BFA', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#A78BFA' } },
  { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#A78BFA', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#A78BFA' } },
  { id: 'e4-5', source: '4', target: '5', animated: true, style: { stroke: '#3B6FE3', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#3B6FE3' } },
  { id: 'e4-6', source: '4', target: '6', animated: true, style: { stroke: '#88C057', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#88C057' } },
];

const COT_STEPS = [
  {
    id: 'step-1', step: 1, agent: 'SENTINEL-INVESTIGATOR',
    action: 'Tool: inspect_process(pid=4892, host="Host-DX9")',
    finding: 'Process powershell.exe (PID 4892) spawned by winword.exe. Unusual parent-child relationship.',
    confidence: 91, mitre: 'T1059.001',
  },
  {
    id: 'step-2', step: 2, agent: 'SENTINEL-INVESTIGATOR',
    action: 'Tool: audit_ad_privileges(entity_id="CORP\\\\jdoe")',
    finding: 'User jdoe has unexpected membership in Domain Admins added 02:14:33 ago. Change not in change log.',
    confidence: 97, mitre: 'T1078',
  },
  {
    id: 'step-3', step: 3, agent: 'SENTINEL-MALWARE-PATH',
    action: 'Tool: analyse_process(pid=4892, host="Host-DX9")',
    finding: 'Memory region 0x7ff82a000 contains encoded payload. De-obfuscated: Invoke-Mimikatz -DumpCreds.',
    confidence: 99, mitre: 'T1003',
  },
  {
    id: 'step-4', step: 4, agent: 'SENTINEL-CORRELATOR',
    action: 'RAG Query: similar credential-dump + lateral-movement patterns',
    finding: 'Pattern matches COBALT STRIKE campaign blueprint seen 3 weeks ago (INC-2025-887). Confidence: HIGH.',
    confidence: 88, mitre: 'T1021',
  },
  {
    id: 'step-5', step: 5, agent: 'SENTINEL-INVESTIGATOR',
    action: 'Synthesis: Generating final conclusion',
    finding: 'CONCLUSION: Active hands-on intrusion by threat actor targeting DC-01. Immediate isolation recommended.',
    confidence: 95, mitre: null,
  },
];

const HITL_QUEUE = [
  {
    id: 'hitl-1', severity: 'CRITICAL', asset: 'Switch-04', action: 'VLAN Isolation',
    agent: 'SENTINEL-RESPONDER', risk: 'HIGH — may disrupt 12 connected endpoints.',
    timestamp: '22:31:44',
  },
  {
    id: 'hitl-2', severity: 'HIGH', asset: 'Host-DX9', action: 'Process Kill: PID 4892',
    agent: 'SENTINEL-RESPONDER', risk: 'LOW — process confirmed malicious.',
    timestamp: '22:32:11',
  },
  {
    id: 'hitl-3', severity: 'MEDIUM', asset: 'CORP\\\\jdoe', action: 'Account Disable',
    agent: 'SENTINEL-GATEKEEPER', risk: 'MEDIUM — account may be used by legitimate user concurrently.',
    timestamp: '22:33:05',
  },
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function CoTStep({ step, expanded, onToggle }) {
  const confColor = step.confidence > 90 ? '#88C057' : step.confidence > 75 ? '#E5A862' : '#EF4444';
  return (
    <div className="rounded-lg overflow-hidden" style={{ border: '1px solid #1F2937', background: '#0d1117' }}>
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 transition-colors text-left">
        <span className="flex-shrink-0 w-5 h-5 rounded flex items-center justify-center text-xs terminal font-bold"
          style={{ background: '#1F2937', color: '#6B7280' }}>
          {step.step}
        </span>
        <span className="flex-1 text-xs" style={{ color: '#CBD5E1' }}>{step.action}</span>
        <div className="flex items-center gap-2 flex-shrink-0">
          {step.mitre && (
            <span className="text-xs terminal px-1.5 py-0.5 rounded"
              style={{ background: '#D84C7F11', color: '#D84C7F', border: '1px solid #D84C7F22' }}>
              {step.mitre}
            </span>
          )}
          <span className="text-xs terminal font-bold" style={{ color: confColor }}>{step.confidence}%</span>
          {expanded ? <ChevronDown size={12} style={{ color: '#6B7280' }} /> : <ChevronRight size={12} style={{ color: '#6B7280' }} />}
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3 border-t" style={{ borderColor: '#1F2937' }}>
          <div className="flex items-center gap-1.5 mt-2 mb-1.5">
            <User size={10} style={{ color: '#3B6FE3' }} />
            <span className="text-xs terminal" style={{ color: '#3B6FE3' }}>{step.agent}</span>
          </div>
          <p className="text-xs leading-relaxed" style={{ color: '#9CA3AF' }}>
            {step.finding}
          </p>
          <div className="mt-2 h-1 rounded-full overflow-hidden" style={{ background: '#1F2937' }}>
            <div className="h-full rounded-full" style={{ width: `${step.confidence}%`, background: confColor, transition: 'width 0.5s ease' }} />
          </div>
        </div>
      )}
    </div>
  );
}

function HitlCard({ item, onApprove, onReject, isAdmin }) {
  const sevColor = item.severity === 'CRITICAL' ? '#EF4444' : item.severity === 'HIGH' ? '#E5A862' : '#3B6FE3';
  return (
    <div className="rounded-lg p-3 animate-slide-in-up"
      style={{ background: '#111827', border: `1px solid ${sevColor}33` }}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full animate-blink flex-shrink-0" style={{ background: sevColor }} />
          <span className="text-xs terminal font-bold" style={{ color: sevColor }}>{item.severity}</span>
          <span className="text-xs terminal" style={{ color: '#6B7280' }}>{item.timestamp}</span>
        </div>
        <span className="text-xs terminal" style={{ color: '#4B5563' }}>{item.id}</span>
      </div>
      <p className="text-xs font-bold mb-0.5" style={{ color: '#E2E8F0' }}>
        {item.action}
      </p>
      <p className="text-xs terminal mb-1" style={{ color: '#93C5FD' }}>Asset: {item.asset}</p>
      <p className="text-xs italic mb-3" style={{ color: '#6B7280' }}>⚠ {item.risk}</p>
      <div className="flex gap-2">
        <button 
          onClick={() => isAdmin && onApprove(item)}
          disabled={!isAdmin}
          className={`flex-1 flex items-center justify-center gap-1 text-xs terminal py-1.5 rounded transition-all ${
            !isAdmin ? 'opacity-50 cursor-not-allowed bg-white/5' : 'hover:brightness-125 bg-[#88C05720] border border-[#88C05733] text-[#88C057]'
          }`}>
          {isAdmin ? <Check size={11} /> : <Lock size={11} />} {isAdmin ? 'Approve' : 'Locked'}
        </button>
        <button 
          onClick={() => isAdmin && onReject(item)}
          disabled={!isAdmin}
          className={`flex-1 flex items-center justify-center gap-1 text-xs terminal py-1.5 rounded transition-all ${
            !isAdmin ? 'opacity-50 cursor-not-allowed bg-white/5' : 'hover:brightness-125 bg-[#EF444420] border border-[#EF444433] text-[#EF4444]'
          }`}>
          {isAdmin ? <X size={11} /> : null} {isAdmin ? 'Reject' : 'View Only'}
        </button>
      </div>
    </div>
  );
}

function InvestigationsSidebar({ investigations }) {
  return (
    <div className="w-80 border-l flex flex-col flex-shrink-0 animate-slide-in-right" 
         style={{ borderColor: '#1F2937', background: '#0d1117' }}>
      <div className="p-4 border-b" style={{ borderColor: '#1F2937' }}>
        <div className="flex items-center justify-between mb-4">
          <span className="text-[10px] terminal font-bold tracking-widest text-[#4B5563]">MISSION CONTROL</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] animate-pulse" />
        </div>
        
        <div className="flex items-center gap-2 p-2.5 rounded border mb-2 group transition-all"
             style={{ background: '#EF444408', border: '1px solid #EF444440' }}>
          <ShieldAlert size={14} className="text-[#EF4444]" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold terminal text-[#EF4444]">CAMPAIGN ACTIVE</span>
            <span className="text-xs font-bold terminal text-[#E2E8F0]">ALPHA-7</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] terminal font-bold text-[#6B7280]">OPEN INVESTIGATIONS</span>
          <span className="text-[10px] terminal text-[#4B5563]">{investigations.length} ACTIVE</span>
        </div>

        {investigations.map(inv => (
          <div key={inv.id} className="group cursor-pointer">
            <div className="flex items-start gap-3 p-3 rounded-lg border border-transparent hover:border-[#3B6FE340] hover:bg-[#3B6FE305] transition-all">
              <div className="mt-1 w-1 h-10 rounded-full flex-shrink-0" 
                   style={{ background: inv.severity === 'CRITICAL' ? '#EF4444' : inv.severity === 'HIGH' ? '#E5A862' : '#3B6FE3' }} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] terminal font-bold" style={{ color: '#4B5563' }}>{inv.id}</span>
                  <span className="text-[9px] terminal px-1.5 py-0.5 rounded uppercase" 
                        style={{ background: '#1F2937', color: '#9CA3AF' }}>{inv.status}</span>
                </div>
                <h4 className="text-xs font-bold text-[#E2E8F0] mb-1 truncate">{inv.title}</h4>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] terminal" style={{ color: '#6B7280' }}>Agent: {inv.assigned_agent}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function InvestigationCanvas() {
  const { user } = useAuth();
  const { pendingActions, approveAction, rejectAction, investigations } = useSOC();
  const isAdmin = user?.role === 'admin';

  const [activeTab, setActiveTab] = useState('graph');
  const [expandedSteps, setExpandedSteps] = useState({});
  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const toggleStep = (id) => setExpandedSteps(p => ({ ...p, [id]: !p[id] }));
  const handleApprove = (item) => approveAction(item.id);
  const handleReject = (item) => rejectAction(item.id);

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header / Tabs */}
      <div className="flex items-center border-b flex-shrink-0" style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        {[
          { id: 'graph', label: '⬡ Attack Chain', icon: GitBranch },
          { id: 'cot',   label: '🧠 CoT Explorer', icon: null },
          { id: 'hitl',  label: `⚠ HITL Queue (${pendingActions.length})`, icon: null },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className="text-xs terminal px-4 py-3 transition-all"
            style={{
              color: activeTab === tab.id ? '#E2E8F0' : '#6B7280',
              borderBottom: activeTab === tab.id ? '2px solid #D84C7F' : '2px solid transparent',
            }}>
            {tab.label}
          </button>
        ))}

        <div className="ml-auto pr-4 flex items-center gap-2">
          <span className="text-xs terminal px-2 py-1 rounded"
            style={{ background: '#EF444418', color: '#EF4444', border: '1px solid #EF444430' }}>
            CAMPAIGN: ALPHA-7 ACTIVE
          </span>
        </div>
      </div>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Workspace */}
        <div className="flex-1 flex flex-col min-w-0">
        {activeTab === 'graph' && (
          <div style={{ height: '100%', width: '100%' }}>
            {mounted ? (
              <ReactFlow
                nodes={nodes} edges={edges}
                onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
                proOptions={{ hideAttribution: true }}>
                <Background color="#1F2937" gap={20} />
                <Controls style={{ background: '#111827', border: '1px solid #1F2937', borderRadius: 8 }} />
              </ReactFlow>
            ) : (
              <div className="h-full flex items-center justify-center">
                 <div className="w-8 h-8 border-2 border-[#D84C7F] border-t-transparent rounded-full animate-spin" />
              </div>
            )}
          </div>
        )}

        {activeTab === 'cot' && (
          <div className="h-full flex flex-col">
            <div className="px-4 pt-3 pb-2 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
              <p className="text-xs terminal" style={{ color: '#6B7280' }}>
                SENTINEL-INVESTIGATOR chain-of-thought for{' '}
                <span style={{ color: '#D84C7F' }}>INC-2026-041 / ALT-004</span>
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {COT_STEPS.map(s => (
                <CoTStep key={s.id} step={s} expanded={!!expandedSteps[s.id]} onToggle={() => toggleStep(s.id)} />
              ))}
            </div>
          </div>
        )}

        {activeTab === 'hitl' && (
          <div className="h-full flex flex-col">
            <div className="px-4 pt-3 pb-2 border-b flex-shrink-0" style={{ borderColor: '#1F2937' }}>
              <p className="text-xs terminal" style={{ color: '#6B7280' }}>
                Actions requiring manual approval before execution.{' '}
                <span style={{ color: '#E5A862' }}>{pendingActions.length} pending</span>
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {pendingActions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-2">
                  <Check size={32} style={{ color: '#88C057' }} />
                  <p className="terminal text-xs" style={{ color: '#4B5563' }}>All actions reviewed</p>
                </div>
              ) : (
                pendingActions.map(item => (
                  <HitlCard key={item.id} item={item} onApprove={handleApprove} onReject={handleReject} isAdmin={isAdmin} />
                ))
              )}
            </div>
          </div>
        )}
        </div>

        {/* Sidebar */}
        <InvestigationsSidebar investigations={investigations} />
      </div>
    </div>
  );
}

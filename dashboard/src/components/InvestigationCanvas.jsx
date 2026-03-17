import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
  Background, Controls, MiniMap,
  useNodesState, useEdgesState, addEdge, MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ChevronDown, ChevronRight, Clock, Check, X, ShieldAlert, GitBranch, User } from 'lucide-react';

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

function HitlCard({ item, onApprove, onReject }) {
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
        <button onClick={() => onApprove(item)}
          className="flex-1 flex items-center justify-center gap-1 text-xs terminal py-1.5 rounded hover:brightness-125 transition-all"
          style={{ background: '#88C05720', color: '#88C057', border: '1px solid #88C05733' }}>
          <Check size={11} /> Approve
        </button>
        <button onClick={() => onReject(item)}
          className="flex-1 flex items-center justify-center gap-1 text-xs terminal py-1.5 rounded hover:brightness-125 transition-all"
          style={{ background: '#EF444420', color: '#EF4444', border: '1px solid #EF444433' }}>
          <X size={11} /> Reject
        </button>
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function InvestigationCanvas() {
  const [nodes, onNodesChange] = useNodesState(INITIAL_NODES);
  const [edges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
  const [expandedSteps, setExpandedSteps] = useState({ 'step-5': true });
  const [hitlItems, setHitlItems] = useState(HITL_QUEUE);
  const [activeTab, setActiveTab] = useState('graph'); // 'graph' | 'cot' | 'hitl'

  const toggleStep = (id) => setExpandedSteps(p => ({ ...p, [id]: !p[id] }));
  const handleApprove = (item) => setHitlItems(p => p.filter(i => i.id !== item.id));
  const handleReject = (item) => setHitlItems(p => p.filter(i => i.id !== item.id));

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header / Tabs */}
      <div className="flex items-center border-b flex-shrink-0" style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        {[
          { id: 'graph', label: '⬡ Attack Chain', icon: GitBranch },
          { id: 'cot',   label: '🧠 CoT Explorer', icon: null },
          { id: 'hitl',  label: `⚠ HITL Queue (${hitlItems.length})`, icon: null },
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

      {/* Content */}
      <div className="flex-1 min-h-0">
        {activeTab === 'graph' && (
          <div style={{ height: '100%', width: '100%' }}>
            <ReactFlow
              nodes={nodes} edges={edges}
              onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
              fitView proOptions={{ hideAttribution: true }}>
              <Background color="#1F2937" gap={20} />
              <Controls style={{ background: '#111827', border: '1px solid #1F2937', borderRadius: 8 }} />
              <MiniMap
                style={{ background: '#0d1117', border: '1px solid #1F2937' }}
                nodeColor={n => {
                  if (n.style?.border?.includes('D84C7F')) return '#D84C7F';
                  if (n.style?.border?.includes('E5A862')) return '#E5A862';
                  if (n.style?.border?.includes('EF4444')) return '#EF4444';
                  if (n.style?.border?.includes('A78BFA')) return '#A78BFA';
                  if (n.style?.border?.includes('3B6FE3')) return '#3B6FE3';
                  if (n.style?.border?.includes('88C057')) return '#88C057';
                  return '#4B5563';
                }}
              />
            </ReactFlow>
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
                <span style={{ color: '#E5A862' }}>{hitlItems.length} pending</span>
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {hitlItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-2">
                  <Check size={32} style={{ color: '#88C057' }} />
                  <p className="terminal text-xs" style={{ color: '#4B5563' }}>All actions reviewed</p>
                </div>
              ) : (
                hitlItems.map(item => (
                  <HitlCard key={item.id} item={item} onApprove={handleApprove} onReject={handleReject} />
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState, useRef, useCallback } from 'react';

// Store
import { SOCProvider, useSOC } from './store/SOCContext';

// Core layout
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import BottomDock from './components/BottomDock';

// Investigation workspace
import EntityGraph from './components/EntityGraph';
import AgentTimeline from './components/AgentTimeline';
import EvidenceInspector from './components/EvidenceInspector';
import InsightLayer from './components/InsightLayer';

// Nav views
import AlertQueue from './components/AlertQueue';
import InvestigationGallery from './components/InvestigationGallery';
import AgentFleetMonitor from './components/AgentFleetMonitor';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import SimulationMode from './components/SimulationMode';

// Sub-panels
import HypothesisPanel from './components/HypothesisPanel';
import AIInsightCards from './components/AIInsightCards';
import InterventionConsole from './components/InterventionConsole';

// Overlays
import BlastRadiusSimulator from './components/BlastRadiusSimulator';
import AICopilot from './components/AICopilot';
import CommandPalette from './components/CommandPalette';
import ApprovalModal from './components/ApprovalModal';
import ExplainModal from './components/ExplainModal';
import EntityPanel from './components/EntityPanel';
import AutonomyWidget from './components/AutonomyWidget';

import './index.css';

// ── Resize Divider ─────────────────────────────────────────────────────
function Divider({ onDrag, direction = 'horizontal' }) {
  const dragging = useRef(false);
  const last = useRef(0);
  const onMouseDown = (e) => {
    dragging.current = true;
    last.current = direction === 'horizontal' ? e.clientX : e.clientY;
    const onMove = (e) => {
      if (!dragging.current) return;
      const curr = direction === 'horizontal' ? e.clientX : e.clientY;
      onDrag(curr - last.current);
      last.current = curr;
    };
    const onUp = () => { dragging.current = false; window.removeEventListener('mousemove', onMove); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp, { once: true });
  };
  return (
    <div onMouseDown={onMouseDown}
      className="flex-shrink-0 flex items-center justify-center group transition-all"
      style={{
        width: direction === 'horizontal' ? 5 : '100%',
        height: direction === 'vertical' ? 5 : '100%',
        background: '#1F2937',
        cursor: direction === 'horizontal' ? 'col-resize' : 'row-resize',
      }}>
      <div className="opacity-0 group-hover:opacity-100 transition-opacity"
        style={{
          width: direction === 'horizontal' ? 2 : 24,
          height: direction === 'horizontal' ? 24 : 2,
          background: '#3B6FE3', borderRadius: 2,
        }} />
    </div>
  );
}

// ── Permissions placeholder ────────────────────────────────────────────
function Permissions() {
  return (
    <div className="flex flex-col h-full items-center justify-center gap-3" style={{ background: '#0B1117' }}>
      <span style={{ fontSize: 32 }}>🔒</span>
      <p className="text-sm font-bold" style={{ color: '#E5A862' }}>Permissions & RBAC</p>
      <p className="text-xs terminal" style={{ color: '#4B5563' }}>Role-based access control management coming soon.</p>
    </div>
  );
}

// ── Tri-pane investigation workspace ──────────────────────────────────
function InvestigationWorkspace() {
  const { selectedEntity } = useSOC();
  const [leftW, setLeftW] = useState(280);
  const [rightW, setRightW] = useState(300);
  const [insightH, setInsightH] = useState(152);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);

  const entityPanelW = selectedEntity ? 260 : 0;

  return (
    <div className="flex h-full">
      {/* LEFT: Entity Graph */}
      {leftCollapsed ? (
        <button onClick={() => setLeftCollapsed(false)}
          className="flex-shrink-0 w-7 flex items-center justify-center border-r hover:brightness-125 transition-all"
          style={{ background: '#0d1117', borderColor: '#1F2937', cursor: 'pointer' }}>
          <span className="terminal text-xs" style={{ color: '#3B6FE3', writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>▷ ENTITY GRAPH</span>
        </button>
      ) : (
        <div className="flex flex-col border-r flex-shrink-0" style={{ width: leftW, borderColor: '#1F2937' }}>
          <div className="flex items-center justify-end px-2 py-1 flex-shrink-0" style={{ background: '#0B1117' }}>
            <button onClick={() => setLeftCollapsed(true)} className="text-xs terminal px-1.5 py-0.5 rounded hover:bg-white/5 transition-colors" style={{ color: '#4B5563' }}>←</button>
          </div>
          <div className="flex-1 min-h-0"><EntityGraph /></div>
        </div>
      )}
      {!leftCollapsed && <Divider onDrag={dx => setLeftW(w => Math.max(140, Math.min(w + dx, 600)))} />}

      {/* CENTER: Timeline + Insights */}
      <div className="flex-1 flex flex-col min-w-0">
        <div style={{ flex: 1, minHeight: 0 }}><AgentTimeline /></div>
        <Divider onDrag={dy => setInsightH(h => Math.max(80, Math.min(h - dy, 280)))} direction="vertical" />
        <div style={{ height: insightH, flexShrink: 0, borderTop: '1px solid #1F2937' }}><InsightLayer /></div>
      </div>

      <Divider onDrag={dx => setRightW(w => Math.max(140, Math.min(w - dx, 600)))} />

      {/* RIGHT: Evidence Inspector */}
      {rightCollapsed ? (
        <button onClick={() => setRightCollapsed(false)}
          className="flex-shrink-0 w-7 flex items-center justify-center border-l hover:brightness-125 transition-all"
          style={{ background: '#0d1117', borderColor: '#1F2937', cursor: 'pointer' }}>
          <span className="terminal text-xs" style={{ color: '#D84C7F', writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>▷ EVIDENCE</span>
        </button>
      ) : (
        <div className="flex flex-col border-l flex-shrink-0" style={{ width: rightW, borderColor: '#1F2937' }}>
          <div className="flex items-center justify-end px-2 py-1 flex-shrink-0" style={{ background: '#0B1117' }}>
            <button onClick={() => setRightCollapsed(true)} className="text-xs terminal px-1.5 py-0.5 rounded hover:bg-white/5 transition-colors" style={{ color: '#4B5563' }}>→</button>
          </div>
          <div className="flex-1 min-h-0"><EvidenceInspector /></div>
        </div>
      )}

      {/* ENTITY DETAIL: slides in from far right */}
      {selectedEntity && (
        <>
          <div className="w-px" style={{ background: '#1F2937' }} />
          <div style={{ width: entityPanelW, flexShrink: 0, transition: 'width 0.25s' }}>
            <EntityPanel />
          </div>
        </>
      )}
    </div>
  );
}

// ── Investigation view with sub-navigation ────────────────────────────
const INV_SUBNAV = [
  { id: 'workspace',  label: 'Workspace' },
  { id: 'hypothesis', label: 'Hypotheses' },
  { id: 'insights',   label: 'AI Insights' },
  { id: 'console',    label: 'Intervention' },
];

function InvestigationsView({ onOpenBlast }) {
  const [sub, setSub] = useState('workspace');
  const { pendingActions, setApprovalAction } = useSOC();

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center border-b flex-shrink-0" style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        {INV_SUBNAV.map(s => (
          <button key={s.id} onClick={() => setSub(s.id)}
            className="text-xs terminal px-4 py-2.5 transition-all"
            style={{ color: sub === s.id ? '#E2E8F0' : '#6B7280', borderBottom: sub === s.id ? '2px solid #D84C7F' : '2px solid transparent' }}>
            {s.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2 pr-3">
          {pendingActions.length > 0 && (
            <button onClick={() => setApprovalAction(pendingActions[0])}
              className="text-xs terminal px-2.5 py-1 rounded animate-pulse hover:brightness-125 transition-all"
              style={{ background: '#E5A86218', color: '#E5A862', border: '1px solid #E5A86233' }}>
              ⚠ {pendingActions.length} Approval{pendingActions.length > 1 ? 's' : ''} Pending
            </button>
          )}
          <button onClick={onOpenBlast}
            className="text-xs terminal px-2.5 py-1 rounded my-1 hover:brightness-125 transition-all"
            style={{ background: '#EF444420', color: '#EF4444', border: '1px solid #EF444433' }}>
            ☢ Blast Radius
          </button>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        {sub === 'workspace'  && <InvestigationWorkspace />}
        {sub === 'hypothesis' && <HypothesisPanel />}
        {sub === 'insights'   && <AIInsightCards />}
        {sub === 'console'    && <InterventionConsole />}
      </div>
    </div>
  );
}

// ── Inner app — uses SOC context ──────────────────────────────────────
function DashboardInner() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeNav, setActiveNav] = useState('Investigations');
  const [blastOpen, setBlastOpen] = useState(false);
  const [copilotOpen, setCopilotOpen] = useState(false);

  const { approvalAction, explainEvent, cmdPaletteOpen, autonomy, pendingActions } = useSOC();

  const sidebarW  = sidebarCollapsed ? 56 : 220;
  const headerH   = 56;
  const dockH     = 64;
  const copilotW  = copilotOpen ? 360 : 0;

  const handleNav = useCallback((navItem) => {
    setActiveNav(navItem);
  }, []);

  const renderView = () => {
    switch (activeNav) {
      case 'Investigations': return <InvestigationsView onOpenBlast={() => setBlastOpen(true)} />;
      case 'Alert Queue':    return <AlertQueue />;
      case 'Agents':         return <AgentFleetMonitor />;
      case 'Analytics':      return <AnalyticsDashboard />;
      case 'Permissions':    return <Permissions />;
      case 'Simulation Mode': return <SimulationMode />;
      default: return <InvestigationsView onOpenBlast={() => setBlastOpen(true)} />;
    }
  };

  return (
    <div className="bg-app" style={{ height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Header */}
      <Header />

      {/* Copilot + Cmd+K hint in header area */}
      <div className="fixed top-2.5 z-[60] flex items-center gap-2" style={{ right: copilotW + 12, transition: 'right 0.3s' }}>
        {/* Autonomy indicator */}
        <span className="text-xs terminal px-2 py-1 rounded"
          style={{ background: '#D84C7F18', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
          AI {autonomy.level}%
        </span>
        {/* Cmd+K hint */}
        <button
          onClick={() => useSOC && document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, bubbles: true }))}
          className="hidden sm:flex items-center gap-1 text-xs terminal px-2 py-1 rounded hover:bg-white/5 transition-colors"
          style={{ color: '#4B5563', border: '1px solid #1F2937' }}>
          <kbd>⌘K</kbd>
        </button>
        {/* Copilot button */}
        <button
          onClick={() => setCopilotOpen(v => !v)}
          className="flex items-center gap-1.5 text-xs terminal px-3 py-1.5 rounded-lg hover:brightness-125 transition-all"
          style={{ background: copilotOpen ? '#D84C7F22' : '#111827', color: '#D84C7F', border: '1px solid #D84C7F44' }}>
          ✦ Copilot
        </button>
      </div>

      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(v => !v)}
        activeNav={activeNav}
        onNavChange={setActiveNav}
      />

      {/* Main body */}
      <div style={{
        position: 'fixed',
        top: headerH, left: sidebarW, right: copilotW, bottom: dockH,
        display: 'flex', flexDirection: 'column',
        transition: 'left 0.3s, right 0.3s',
        overflow: 'hidden',
      }}>
        {renderView()}
      </div>

      {/* Copilot panel */}
      {copilotOpen && (
        <div style={{
          position: 'fixed', top: headerH, right: 0, bottom: dockH,
          width: copilotW, borderLeft: '1px solid #1F2937', zIndex: 40,
          transition: 'width 0.3s',
        }}>
          <AICopilot onClose={() => setCopilotOpen(false)} />
        </div>
      )}

      {/* Bottom Dock */}
      <div style={{
        position: 'fixed', bottom: 0, left: sidebarW, right: 0,
        height: dockH, zIndex: 30, transition: 'left 0.3s',
      }}>
        <BottomDock />
      </div>

      {/* Global overlays */}
      <CommandPalette onNavigate={handleNav} onOpenCopilot={() => setCopilotOpen(true)} />
      <ApprovalModal />
      <ExplainModal />
      {blastOpen && <BlastRadiusSimulator onClose={() => setBlastOpen(false)} />}
    </div>
  );
}

// ── Root: wrap with provider ───────────────────────────────────────────
export default function App() {
  return (
    <SOCProvider>
      <DashboardInner />
    </SOCProvider>
  );
}

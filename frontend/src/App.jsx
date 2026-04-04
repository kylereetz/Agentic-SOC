import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';

// Auth & Context
import { AuthProvider, useAuth } from './store/AuthContext';
import { SOCProvider, useSOC } from './store/SOCContext';
import LoginPage from './components/LoginPage';

// Core Dashboard Components
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import InvestigationCanvas from './components/InvestigationCanvas';
import AlertQueue from './components/AlertQueue';
import HiveHealth from './components/HiveHealth';
import ThreatTelemetry from './components/ThreatTelemetry';
import GovernanceDashboard from './components/GovernanceDashboard';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import SimulationMode from './components/SimulationMode';
import CyberRange from './components/CyberRange';
import AuditDiscoveryLaunchpad from './components/AuditDiscoveryLaunchpad';
import PermissionsView from './components/PermissionsView';
import BottomDock from './components/BottomDock';
import NetflowView from './components/NetflowView';
import HostDrilldownPanel from './components/HostDrilldownPanel';
import LogIntegrityMonitor from './components/LogIntegrityMonitor';
import EntityGraph from './components/EntityGraph';
import CaseHistoryView from './components/CaseHistoryView';
import PatchPilotView from './components/PatchPilotView';
import ForensicsPanel from './components/ForensicsPanel';
import MalwarePathologistView from './components/MalwarePathologistView';
import HeatmapView from './components/HeatmapView';

import { 
  ShieldAlert, 
  GitBranch, 
  Bot, 
  Activity, 
  Shield, 
  BarChart2, 
  Lock, 
  TrendingUp, 
  AlertTriangle 
} from 'lucide-react';

// Overlays & Utilities
import CommandPalette from './components/CommandPalette';
import ApprovalModal from './components/ApprovalModal';
import ExplainModal from './components/ExplainModal';
import ChitChat from './components/ChitChat';
import BlastRadiusSimulator from './components/BlastRadiusSimulator';

import './index.css';

// ── Global Error Boundary ──────────────────────────────────────────────
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-black flex items-center justify-center p-12 text-red-500 terminal">
          <div>
            <h1 className="text-2xl font-bold mb-4">CRITICAL SYSTEM FAILURE</h1>
            <p className="mb-8">An unrecoverable error occurred in the dashboard engine.</p>
            <pre className="p-4 bg-red-950/20 border border-red-900 rounded-lg text-xs overflow-auto max-w-2xl max-h-96">
              {this.state.error?.stack || this.state.error?.message}
            </pre>
            <button 
              onClick={() => window.location.reload()}
              className="mt-8 px-6 py-2 border border-red-500 rounded hover:bg-red-500/10 active:scale-95 transition-all">
              REBOOT SYSTEM
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Inner app — uses SOC context ──────────────────────────────────────
function DashboardInner() {
  const { user, logout, loading } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeNav, setActiveNav] = useState('Investigations');
  const [blastOpen, setBlastOpen] = useState(false);
  const [chitchatOpen, setChitChatOpen] = useState(false);

  const { approvalAction, explainEvent, cmdPaletteOpen, autonomy, pendingActions } = useSOC();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B1117]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-[#3B6FE3] border-t-transparent rounded-full animate-spin" />
          <p className="terminal text-xs text-[#4B5563]">SYNCHRONIZING SECURE TUNNEL...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  // Sidebar: collapses to icon-only (56px) or expands to clamp(180px, 15vw, 220px)
  const sidebarW  = sidebarCollapsed ? 56 : 'clamp(180px, 15vw, 220px)';
  const headerH   = 56;
  const dockH     = 64;
  // ChitChat: clamp between 300px and 380px, capped at 30vw to avoid eating the main area
  const chitchatW = chitchatOpen ? 'clamp(300px, 25vw, 380px)' : 0;

  const handleNav = (navItem) => setActiveNav(navItem);

  const renderView = () => {
    switch (activeNav) {
      case 'Investigations': return <InvestigationCanvas onOpenBlast={() => setBlastOpen(true)} />;
      case 'Discovery / Audit': return <AuditDiscoveryLaunchpad />;
      case 'Alert Queue':    return <AlertQueue />;
      case 'Log Guardian':   return <LogIntegrityMonitor />;
      case 'Agents':         return <HiveHealth />;
      case 'Threat Intel':   return <ThreatTelemetry />;
      case 'Netflow / Traffic': return <NetflowView />;
      case 'Topology':         return <EntityGraph />;
      case 'Case History':     return <CaseHistoryView />;
      case 'Patch Pilot':      return <PatchPilotView />;
      case 'Forensics':         return <ForensicsPanel />;
      case 'Malware Lab':       return <MalwarePathologistView />;
      case 'Risk Heatmap':      return <HeatmapView />;
      case 'Governance':     return <GovernanceDashboard />;
      case 'Analytics':      return <AnalyticsDashboard />;
      case 'Adversary Sim':  return <CyberRange />;
      case 'Permissions':     return <PermissionsView />;
      case 'Simulation Mode': return <SimulationMode />;
      default: return <InvestigationCanvas onOpenBlast={() => setBlastOpen(true)} />;
    }
  };

  return (
    <div className="bg-app" style={{ minHeight: '100vh', minWidth: 1152, overflowX: 'auto' }}>
      {/* Header */}
      <Header 
        chitchatOpen={chitchatOpen} 
        onToggleChitChat={() => setChitChatOpen(!chitchatOpen)} 
      />

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
        top: headerH, left: sidebarW, right: chitchatW, bottom: dockH,
        display: 'flex', flexDirection: 'column',
        transition: 'left 0.3s, right 0.3s',
        overflow: 'hidden',
      }}>
        {renderView()}
      </div>

      {/* ChitChat panel */}
      {chitchatOpen && (
        <div style={{
          position: 'fixed', top: headerH, right: 0, bottom: dockH,
          width: chitchatW, borderLeft: '1px solid #1F2937', zIndex: 40,
          transition: 'width 0.3s',
        }}>
          <ChitChat onClose={() => setChitChatOpen(false)} />
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
      <CommandPalette onNavigate={handleNav} onOpenChitChat={() => setChitChatOpen(true)} />
      <ApprovalModal />
      <ExplainModal />
      <HostDrilldownPanel />
      {blastOpen && <BlastRadiusSimulator onClose={() => setBlastOpen(false)} />}
    </div>
  );
}

// ── Root: wrap with providers ───────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <SOCProvider>
        <ErrorBoundary>
          <DashboardInner />
        </ErrorBoundary>
      </SOCProvider>
    </AuthProvider>
  );
}

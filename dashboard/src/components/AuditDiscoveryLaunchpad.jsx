import React, { useState } from 'react';
import { Search, Network, Database, ShieldAlert, Cpu, CheckCircle, Activity, Play, Settings } from 'lucide-react';
import { useAuth } from '../store/AuthContext';

const AUDIT_STAGES = [
  { id: 'passive', label: 'Phase 1: Passive Sniffing (15s)', expected: 15 },
  { id: 'arp',     label: 'Phase 2: Active ARP Sweep', expected: 12 },
  { id: 'icmp',    label: 'Phase 3: ICMP Sweep', expected: 5 },
  { id: 'ot',      label: 'Phase 4: Industrial OT Probing', expected: 8 },
  { id: 'nist',    label: 'Phase 5: NIST Compliance Mapping', expected: 20 },
  { id: 'local',   label: 'Phase 6: Local OS Hardening', expected: 10 },
];

export default function AuditDiscoveryLaunchpad() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [isRunning, setIsRunning] = useState(false);
  const [activeStage, setActiveStage] = useState(-1);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [inventory, setInventory] = useState([]);

  const addLog = (msg) => {
    setLogs(prev => [...prev.slice(-30), `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const startAudit = () => {
    if (!isAdmin) return;
    setIsRunning(true);
    setActiveStage(0);
    setProgress(0);
    setLogs([]);
    setInventory([]);
    addLog("INITIATING MAIN.PY AUDIT ROUTINE...");

    let currentStage = 0;
    
    const stageRun = () => {
      if (currentStage >= AUDIT_STAGES.length) {
        setIsRunning(false);
        setActiveStage(-1);
        addLog("AUDIT COMPLETED SUCESSFULLY. INVENTORY UPDATED.");
        // Mock inventory updates
        setInventory([
          { ip: '192.168.1.1', mac: 'AA:BB:CC:DD:EE:01', type: 'Gateway' },
          { ip: '192.168.1.10', mac: 'AA:BB:CC:DD:EE:10', type: 'Server (Windows)' },
          { ip: '10.0.0.50', mac: 'AA:BB:CC:DD:EE:50', type: 'OT PLC (Modbus)' },
          { ip: '192.168.1.105', mac: 'AA:BB:CC:DD:EE:A5', type: 'Workstation' },
        ]);
        return;
      }

      addLog(`STARTED: ${AUDIT_STAGES[currentStage].label}`);
      setActiveStage(currentStage);
      let ticks = 0;
      const tId = setInterval(() => {
        ticks++;
        setProgress(Math.round((ticks / AUDIT_STAGES[currentStage].expected) * 100));
        
        if (Math.random() > 0.6) {
          addLog(`... discovering assets on segment.`);
        }

        if (ticks >= AUDIT_STAGES[currentStage].expected) {
          clearInterval(tId);
          addLog(`COMPLETED: ${AUDIT_STAGES[currentStage].label}`);
          currentStage++;
          setTimeout(stageRun, 800);
        }
      }, 500);
    };

    setTimeout(stageRun, 800);
  };

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <Search size={14} style={{ color: '#D84C7F' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            FIRST-RUN AUDIT & DISCOVERY
          </span>
          <span className="terminal text-xs px-2 py-0.5 rounded-full"
            style={{ background: '#1F2937', color: '#6B7280', border: '1px solid #374151' }}>
            ENGINE.CORE.SENTINEL
          </span>
        </div>
        <button
          onClick={startAudit}
          disabled={!isAdmin || isRunning}
          className={`flex items-center gap-2 text-xs terminal px-4 py-2 rounded-lg font-bold transition-all ${
            (!isAdmin || isRunning) ? 'opacity-50 cursor-not-allowed' : 'hover:brightness-125'
          }`}
          style={{
            background: isRunning ? '#1F2937' : '#D84C7F22',
            color: isRunning ? '#6B7280' : '#D84C7F',
            border: `1px solid ${isRunning ? '#374151' : '#D84C7F66'}`,
          }}>
          {isRunning ? <Activity size={13} className="animate-pulse" /> : <Play size={13} />}
          {isRunning ? 'AUDIT IN PROGRESS' : 'LAUNCH MAIN.PY AUDIT'}
        </button>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* LEFT: Stages & Configuration */}
        <div className="flex flex-col p-6 overflow-y-auto" style={{ width: '40%', borderRight: '1px solid #1F2937' }}>
          <p className="text-xs terminal mb-4" style={{ color: '#6B7280' }}>DISCOVERY STAGES</p>
          <div className="space-y-4">
            {AUDIT_STAGES.map((stage, idx) => {
              const isActive = activeStage === idx;
              const isPast = activeStage > idx || activeStage === -1 && inventory.length > 0;
              const color = isActive ? '#D84C7F' : isPast ? '#88C057' : '#374151';
              
              return (
                <div key={stage.id} className="flex items-start gap-4">
                  <div className="flex flex-col items-center mt-0.5">
                    <div className="w-4 h-4 rounded-full flex items-center justify-center"
                      style={{ background: isActive ? `${color}22` : 'transparent', border: `1px solid ${color}` }}>
                      {isPast ? <CheckCircle size={8} style={{ color }} /> : <div className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />}
                    </div>
                    {idx < AUDIT_STAGES.length - 1 && (
                      <div className="w-px h-6 mt-1" style={{ background: isPast ? '#88C057' : '#1F2937' }} />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm font-bold terminal ${isActive ? 'animate-pulse' : ''}`} style={{ color }}>
                      {stage.label}
                    </p>
                    {isActive && (
                      <div className="h-1 rounded-full overflow-hidden mt-2" style={{ background: '#1F2937' }}>
                        <div className="h-full rounded-full transition-all" style={{ width: `${progress}%`, background: color }} />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <p className="text-xs terminal mt-8 mb-4 border-t pt-6" style={{ color: '#6B7280', borderColor: '#1F2937' }}>CONFIGURATION PARAMETERS</p>
          <div className="space-y-3">
             <div className="flex justify-between text-xs terminal p-3 rounded-lg" style={{ background: '#111827', border: '1px solid #1F2937', color: '#9CA3AF' }}>
               <span>TARGET SUBNET</span>
               <span style={{ color: '#3B6FE3' }}>192.168.1.0/24</span>
             </div>
             <div className="flex justify-between text-xs terminal p-3 rounded-lg" style={{ background: '#111827', border: '1px solid #1F2937', color: '#9CA3AF' }}>
               <span>INDUSTRIAL (OT) FLAGS</span>
               <span style={{ color: '#88C057' }}>ENABLED</span>
             </div>
          </div>
        </div>

        {/* RIGHT: Live Feed & Inventory */}
        <div className="flex flex-col flex-1 min-w-0">
          <div className="flex-1 overflow-y-auto p-4 flex flex-col" style={{ borderBottom: '1px solid #1F2937' }}>
            <div className="flex items-center gap-2 mb-3">
              <Network size={12} style={{ color: '#3B6FE3' }} />
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>CLI OUTPUT FEED</span>
            </div>
            <div className="flex-1 rounded-lg p-4 font-mono text-xs overflow-y-auto scanline-overlay"
              style={{ background: '#080c12', color: '#4B5563', border: '1px solid #1F2937' }}>
              {logs.length === 0 && <span className="opacity-50">Awaiting audit launch...</span>}
              {logs.map((log, i) => (
                <div key={i} className="mb-1 leading-relaxed animate-slide-in-up">
                  <span style={{ color: log.includes('STARTED') ? '#D84C7F' : log.includes('COMPLETED') ? '#88C057' : '#4B5563' }}>
                    {log}
                  </span>
                </div>
              ))}
              {isRunning && <span className="typing-cursor" style={{ color: '#D84C7F' }} />}
            </div>
          </div>

          <div className="h-1/3 min-h-[250px] p-4 flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Database size={12} style={{ color: '#88C057' }} />
                <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>DISCOVERED INVENTORY (JSON)</span>
              </div>
              <span className="text-xs terminal" style={{ color: '#88C057' }}>{inventory.length} NODES</span>
            </div>
            <div className="flex-1 rounded-lg p-4 font-mono text-xs overflow-y-auto"
              style={{ background: '#111827', border: '1px solid #1F2937', color: '#E2E8F0' }}>
               {inventory.length === 0 ? (
                 <span style={{ color: '#4B5563' }}>No inventory mapped.</span>
               ) : (
                 <pre>{JSON.stringify(inventory, null, 2)}</pre>
               )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

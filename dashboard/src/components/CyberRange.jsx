import React, { useState, useEffect } from 'react';
import { Target, ShieldAlert, Crosshair, Terminal, Zap, Power, Server, ShieldOff } from 'lucide-react';
import { useAuth } from '../store/AuthContext';

const SIMULATION_SCENARIOS = [
  { id: 'sim-1', name: 'APT29 Lateral Movement', complexity: 'High', mitre: 'T1021, T1550', duration: '45m' },
  { id: 'sim-2', name: 'Ransomware Outbreak (Conti)', complexity: 'Critical', mitre: 'T1486, T1490', duration: '20m' },
  { id: 'sim-3', name: 'Insider Threat: Data Exfil', complexity: 'Medium', mitre: 'T1048, T1567', duration: '60m' },
];

export default function CyberRange() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [activeSim, setActiveSim] = useState(null);
  const [logs, setLogs] = useState([]);
  
  const handleLaunch = (sim) => {
    setActiveSim(sim);
    setLogs([
      `[SYS] Initializing Cyber Range Environment...`,
      `[SYS] Allocating ephemeral target nodes...`,
      `[SYS] Instantiating SENTINEL-RED-TEAM...`,
      `[RED] Loaded objective profile: ${sim.name}`,
    ]);
  };

  const handleStop = () => {
    setActiveSim(null);
    setLogs([]);
  };

  // Mock attack live event generation
  useEffect(() => {
    if (!activeSim) return;
    const t = setInterval(() => {
      const msgs = [
        `[RED] Executing reconnaissance (nmap -sn 10.100.0.0/24)...`,
        `[RED] Found vulnerable service: SMBv1 on 10.100.0.45`,
        `[RED] Attempting credential dumping via LSASS memory...`,
        `[RED] Lateral movement successful to DC-02`,
        `[RED] Deploying staging payload...`,
        `[SYS] Blue Team (TRIAGE) logged anomaly detection`
      ];
      setLogs(prev => [...prev.slice(-40), `[${new Date().toLocaleTimeString()}] ${msgs[Math.floor(Math.random() * msgs.length)]}`]);
    }, 4500);
    return () => clearInterval(t);
  }, [activeSim]);

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <Crosshair size={14} style={{ color: '#EF4444' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            ADVERSARY SIMULATION: CYBER RANGE
          </span>
          <span className="terminal text-xs px-2 py-0.5 rounded-full"
            style={{ background: '#EF444420', color: '#EF4444', border: '1px solid #EF444444' }}>
            SENTINEL-RED-TEAM
          </span>
        </div>
        
        {activeSim && (
          <button
            onClick={handleStop}
            className="flex items-center gap-2 text-xs terminal px-4 py-2 rounded-lg font-bold transition-all hover:brightness-125 focus:outline-none"
            style={{ background: '#EF444422', color: '#EF4444', border: `1px solid #EF444466` }}>
            <Power size={13} />
            TERMINATE SIMULATION
          </button>
        )}
      </div>

      <div className="flex flex-1 min-h-0">
        {/* LEFT: Scenarios */}
        <div className="flex flex-col p-6 overflow-y-auto" style={{ width: '35%', borderRight: '1px solid #1F2937' }}>
          <p className="text-xs terminal mb-4" style={{ color: '#6B7280' }}>AVAILABLE SCENARIOS</p>
          <div className="space-y-3">
            {SIMULATION_SCENARIOS.map(sim => (
              <div key={sim.id} className="p-4 rounded-lg flex flex-col gap-2 transition-all hover:bg-white/5 cursor-pointer"
                style={{ 
                  background: activeSim?.id === sim.id ? '#1A1A1A' : '#111827', 
                  border: `1px solid ${activeSim?.id === sim.id ? '#EF4444' : '#1F2937'}`
                }}
                onClick={() => !activeSim && isAdmin && handleLaunch(sim)}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold truncate" style={{ color: '#E2E8F0' }}>{sim.name}</span>
                  <span className="text-xs terminal" style={{ color: sim.complexity === 'Critical' ? '#EF4444' : '#E5A862' }}>{sim.complexity}</span>
                </div>
                <p className="text-xs terminal" style={{ color: '#6B7280' }}>MITRE: {sim.mitre}</p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-[10px] terminal px-2 py-0.5 rounded" style={{ background: '#1F2937', color: '#9CA3AF' }}>~{sim.duration}</span>
                  {!activeSim && (
                    <span className="text-xs font-bold" style={{ color: isAdmin ? '#EF4444' : '#4B5563' }}>
                      {isAdmin ? 'LAUNCH ➔' : 'LOCKED'}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: Live Cyber Range Feed */}
        <div className="flex flex-col flex-1 min-w-0 p-4">
          <div className="flex items-center justify-between mb-3 flex-shrink-0">
            <div className="flex items-center gap-2">
              <Terminal size={12} style={{ color: '#EF4444' }} />
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>RED TEAM EXFILTRATION FEED</span>
            </div>
            {activeSim && <span className="text-xs terminal animate-pulse" style={{ color: '#EF4444' }}>LIVE ENGAGEMENT: {activeSim.name}</span>}
          </div>
          
          <div className="flex-1 rounded-lg p-4 font-mono text-xs overflow-y-auto scanline-overlay"
            style={{ background: '#080c12', color: '#4B5563', border: '1px solid #1F2937' }}>
            {logs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full opacity-30 gap-3">
                <ShieldOff size={32} />
                <span>Cyber Range offline. Select a scenario to deploy the Red Team.</span>
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="mb-1 leading-relaxed animate-slide-in-up">
                  <span style={{ 
                    color: log.includes('RED]') ? '#EF4444' : 
                          log.includes('SYS]') ? '#6B7280' : '#E5A862'
                  }}>
                    {log}
                  </span>
                </div>
              ))
            )}
            {activeSim && <span className="typing-cursor" style={{ color: '#EF4444' }} />}
          </div>
        </div>
      </div>
    </div>
  );
}

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';

// ── Mock Entity Database ─────────────────────────────────────────────
export const ENTITY_DB = {
  '192.168.1.105': { id: '192.168.1.105', type: 'IP', label: '192.168.1.105', risk: 'Critical', os: 'Windows 10', mac: 'AA:BB:CC:DD:EE:FF', owner: 'KR\\admin', vlan: 'CORP-10', firstSeen: '2023-10-24T12:01:00Z', alerts: ['ALT-001', 'ALT-002'] },
  'Host-DX9':      { id: 'Host-DX9',      type: 'Host', label: 'Host-DX9', risk: 'Critical', os: 'Windows 10 Pro', ip: '192.168.1.105', domain: 'CORP', owner: 'KR\\admin', status: 'ISOLATED', alerts: ['ALT-001', 'ALT-007'] },
  'svchost.exe':   { id: 'svchost.exe',   type: 'Process', label: 'svchost.exe', pid: 9912, parent: 'services.exe', cmdline: 'svchost.exe -k netsvcs -p', hash: 'e3b0c44298fc1c149afbf4c8996fb9', risk: 'Critical', signed: false },
  'KR\\admin':     { id: 'KR\\admin',     type: 'User',    label: 'KR\\admin', department: 'IT', riskScore: 87, lastLogon: '2023-10-24T02:14:00Z', groups: ['Domain Admins', 'Schema Admins'], alerts: ['ALT-002'] },
  'srv-dc01':      { id: 'srv-dc01',      type: 'Host',    label: 'srv-dc01', risk: 'High', os: 'Windows Server 2019', role: 'Domain Controller', ip: '192.168.1.10', status: 'ONLINE' },
  '10.0.0.22':     { id: '10.0.0.22',     type: 'IP',      label: '10.0.0.22', risk: 'Medium', owner: 'KR\\svc_sql', vlan: 'DB-VLAN' },
  'Host-WS4':      { id: 'Host-WS4',      type: 'Host',    label: 'Host-WS4', risk: 'High', os: 'Windows 11', ip: '192.168.1.108', status: 'ONLINE' },
  'OT-PLC-01':     { id: 'OT-PLC-01',     type: 'Host',    label: 'OT-PLC-01', risk: 'Low', os: 'Rockwell RSLogix', ip: '10.0.0.50', protocol: 'Modbus/TCP', status: 'ONLINE' },
};

// ── Mock API Endpoints ───────────────────────────────────────────────
export const mockAPI = {
  '/api/investigations': [
    { id: 'INC-2023-981', severity: 'Critical', stage: 'Investigating', progress: 62, entities: 8,  agent: 'MANAGER-01', title: 'Credential Theft Campaign',  lastActivity: '2m ago' },
    { id: 'INC-2023-980', severity: 'High',     stage: 'Containment',   progress: 85, entities: 4,  agent: 'TRIAGE-01',   title: 'SMB Lateral Movement',       lastActivity: '7m ago' },
    { id: 'INC-2023-979', severity: 'Critical', stage: 'Eradication',   progress: 92, entities: 12, agent: 'MANAGER-01', title: 'Ransomware Staging',         lastActivity: '14m ago' },
    { id: 'INC-2023-978', severity: 'Medium',   stage: 'Triage',        progress: 22, entities: 2,  agent: 'FORENSICS-01',    title: 'DNS Tunneling',              lastActivity: '31m ago' },
  ],
  '/api/agents': [
    { id: 'SENTINEL-ORCHESTRATOR', role: 'Orchestrator',           color: '#D84C7F', status: 'ACTIVE',  task: 'Routing 6 pending alerts', runtime: '12:44', success: 98, tools: 88 },
    { id: 'SENTINEL-TRIAGE',       role: 'TriageAgent',            color: '#3B6FE3', status: 'ACTIVE',  task: 'Classifying incoming EventBus anomalies', runtime: '48:12', success: 92, tools: 1050 },
    { id: 'SENTINEL-CORRELATOR',   role: 'CorrelatorAgent',        color: '#E5A862', status: 'IDLE',    task: 'Awaiting new historical linkages', runtime: '00:00', success: 94, tools: 12 },
    { id: 'SENTINEL-LIBRARIAN',    role: 'LibrarianAgent',         color: '#88C057', status: 'ACTIVE',  task: 'Indexing resolved case data to Vector DB', runtime: '04:12', success: 100, tools: 45 },
    { id: 'SENTINEL-HUNTER',       role: 'HunterAgent',            color: '#D84C7F', status: 'ACTIVE',  task: 'Executing hypothesis-driven threat hunt', runtime: '14:22', success: 87, tools: 67 },
    { id: 'SENTINEL-LOG-GUARDIAN', role: 'LogGuardianAgent',       color: '#3B6FE3', status: 'ACTIVE',  task: 'Normalizing proprietary CEF logs', runtime: '55:10', success: 99, tools: 210 },
    { id: 'SENTINEL-TRAFFIC-SIEVE',role: 'TrafficSieveAgent',      color: '#88C057', status: 'ACTIVE',  task: 'Analyzing netflow for data exfiltration', runtime: '22:15', success: 91, tools: 154 },
    { id: 'SENTINEL-CLOUD-WRAITH', role: 'CloudWraithAgent',       color: '#3B6FE3', status: 'ACTIVE',  task: 'Monitoring AWS IAM CloudTrail anomalies', runtime: '19:30', success: 98, tools: 112 },
    { id: 'SENTINEL-RESPONDER',    role: 'ResponderAgent',         color: '#EF4444', status: 'WAITING', task: 'Waiting for analyst approval', runtime: '02:11', success: 100, tools: 5 },
    { id: 'SENTINEL-GATEKEEPER',   role: 'GatekeeperAgent',        color: '#E5A862', status: 'ACTIVE',  task: 'Auditing impossible travel ID anomalies', runtime: '33:10', success: 95, tools: 201 },
    { id: 'SENTINEL-VANGUARD',     role: 'VanguardAgent',          color: '#3B6FE3', status: 'IDLE',    task: 'Awaiting SBOM composition updates', runtime: '00:00', success: 100, tools: 0 },
    { id: 'SENTINEL-MIRAGE',       role: 'MirageAgent',            color: '#D84C7F', status: 'ACTIVE',  task: 'Monitoring deception honeypot beacons', runtime: '100:10', success: 100, tools: 50 },
    { id: 'SENTINEL-SCOUT',        role: 'ScoutAgent',             color: '#88C057', status: 'ACTIVE',  task: 'Passive network discovery on subnet /24', runtime: '41:15', success: 90, tools: 334 },
    { id: 'SENTINEL-GOVERNOR',     role: 'GovernorAgent',          color: '#E5A862', status: 'ACTIVE',  task: 'Cross-mapping NIST & CMMC controls', runtime: '00:00', success: 98, tools: 0 },
    { id: 'SENTINEL-COMMUNICATOR', role: 'CommunicatorAgent',      color: '#3B6FE3', status: 'ACTIVE',  task: 'Synthesizing executive report', runtime: '01:22', success: 99, tools: 4 },
    { id: 'SENTINEL-WATCHDOG',     role: 'WatchdogAgent',          color: '#EF4444', status: 'ACTIVE',  task: 'Monitoring hive telemetry health & latency', runtime: '124:00', success: 100, tools: 888 },
    { id: 'SENTINEL-RED-TEAM',     role: 'RedTeamAgent',           color: '#EF4444', status: 'IDLE',    task: 'Awaiting cyber range deployment', runtime: '00:00', success: 100, tools: 15 },
  ],
  '/api/evidence': [
    { id: 'EVD-001', source: 'EDR',   timestamp: '14:02:11', agent: 'MANAGER-01', sha256: 'e3b0c44...b855', type: 'Memory Dump',   name: 'HOST-DX9-memdump.dmp', size: '3.2 GB' },
    { id: 'EVD-002', source: 'EDR',   timestamp: '14:02:12', agent: 'MANAGER-01', sha256: 'a8f7c12...d3e1', type: 'Payload',       name: 'ps_payload.b64',       size: '4.1 KB' },
    { id: 'EVD-003', source: 'SIEM',  timestamp: '14:01:55', agent: 'TRIAGE-01',   sha256: 'f2d89ab...cc42', type: 'Network PCAP',  name: 'network_1014.pcap',    size: '22 MB' },
    { id: 'EVD-004', source: 'SOAR',  timestamp: '14:02:14', agent: 'RESPONDER-01',   sha256: 'b1c23ef...aa99', type: 'Report',        name: 'gap_analysis_INC-981.pdf', size: '1.8 MB' },
  ],
  '/api/actions': [
    { id: 'ACT-001', type: 'HOST_ISOLATION',  agent: 'RESPONDER-01', target: 'Host-DX9',   risk: 92, status: 'PENDING', description: 'Isolate Host-DX9 by blocking all inbound/outbound traffic via host-based firewall.', impacted: ['Host-DX9', '192.168.1.105', 'KR\\admin'] },
    { id: 'ACT-002', type: 'ACCOUNT_DISABLE', agent: 'MANAGER-01', target: 'KR\\admin', risk: 74, status: 'PENDING', description: "Disable KR\\admin account in Active Directory to prevent further lateral movement.", impacted: ['KR\\admin', 'srv-dc01'] },
  ],
};

// ── Live Reasoning Event Templates ───────────────────────────────────
const makeEvent = (i) => {
  const templates = [
    { type: 'THOUGHT', agent: 'MANAGER-01', color: '#D84C7F', content: `Detected anomalous beacon from 192.168.1.105 to external C2 server. Interval: 60s. Evaluating pattern similarity to known APT infrastructure.`, entities: ['192.168.1.105'], mitre: 'T1071.001', confidence: 88, tool: 'beacon_analyzer', duration: '2.1s', evidence: ['EVD-003'], reasoning: `Query matched 14 IOCs in internal TI database. Beaconing interval aligns with APT-29 C2 profile. Risk score elevated by 12 points.` },
    { type: 'ACTION',  agent: 'TRIAGE-01',   color: '#3B6FE3', content: null, code: `query_siem --timerange "-1h" --filter "source_ip=192.168.1.105"`, entities: ['192.168.1.105'], mitre: 'T1078', confidence: 91, tool: 'siem_query', duration: '0.8s', evidence: ['EVD-001'], reasoning: `SIEM query to correlate lateral movement events in the last hour. 4 matching events found.` },
    { type: 'OBSERVATION', agent: 'MANAGER-01', color: '#88C057', content: `SIEM returned 4 correlated events. Host-WS4 communicating with same external IP. Expanding blast radius to include Host-WS4 in isolation scope.`, entities: ['Host-WS4', '192.168.1.105'], mitre: 'T1021', confidence: 85, tool: 'correlation_engine', duration: '1.4s', evidence: ['EVD-003'], reasoning: `Two hosts now confirmed communicating with C2 infrastructure. Probability of coordinated attack increased to 94%.` },
    { type: 'THOUGHT',  agent: 'FORENSICS-01',   color: '#D84C7F', content: `Memory analysis of HOST-DX9 dump reveals injected shellcode in svchost.exe PID 9912. Shellcode pattern matches Cobalt Strike beacon.`, entities: ['svchost.exe', 'Host-DX9'], mitre: 'T1055', confidence: 96, tool: 'memory_analyzer', duration: '8.2s', evidence: ['EVD-001'], reasoning: `Shellcode signature matches 98.4% of known Cobalt Strike loader. Injected region: .text segment override at 0x7FF8.` },
    { type: 'ACTION',  agent: 'RESPONDER-01',   color: '#E5A862', content: null, code: `block_firewall --rule OUTBOUND --dst 203.0.113.45 --priority HIGH`, entities: ['192.168.1.105', 'Host-DX9'], mitre: 'T1562.004', confidence: 93, tool: 'firewall_api', duration: '0.3s', evidence: [], reasoning: `C2 IP blocked at perimeter to stop beaconing while investigation continues. Non-disruptive — no internal traffic affected.`, isPending: true },
  ];
  return { ...templates[i % templates.length], id: `EVT-LIVE-${Date.now()}-${i}`, timestamp: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 }) };
};

// ── Autonomy Stats ────────────────────────────────────────────────────
const INITIAL_AUTONOMY = { level: 91, agentActions: 42, humanApproved: 19, humanOverrides: 6, policyOverrides: 3 };

// ── Context ───────────────────────────────────────────────────────────
const SOCContext = createContext(null);

export function SOCProvider({ children }) {
  const { token } = useAuth();
  // Core state
  const [agents, setAgents]           = useState(mockAPI['/api/agents']);
  const [alerts, setAlerts]           = useState([]);
  const [evidence, setEvidence]       = useState(mockAPI['/api/evidence']);
  const [pendingActions, setPending]  = useState(mockAPI['/api/actions']);
  const [autonomy, setAutonomy]       = useState(INITIAL_AUTONOMY);
  const [investigations, setInvestigations] = useState([]);

  // Timeline live stream
  const [timelineEvents, setTimeline] = useState([]);
  const eventCountRef = useRef(0);

  // Entity navigation
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [highlightedNode, setHighlightedNode] = useState(null);
  const [entityFilter, setEntityFilter]     = useState(null); // entity ID to filter timeline by

  // Modals / overlays
  const [approvalAction, setApprovalAction] = useState(null); // action to approve
  const [explainEvent, setExplainEvent]     = useState(null); // timeline event to explain
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false);

  // Replay
  const [replayProgress, setReplayProgress] = useState(72);
  const [replayPlaying, setReplayPlaying]   = useState(false);

  // ── Live event stream ───────────────────────────────────────────────
  useEffect(() => {
    // Inject an event every 6–10 seconds
    const tick = () => {
      const evt = makeEvent(eventCountRef.current++);
      setTimeline(prev => [...prev, evt]);

      // Highlight referenced nodes
      if (evt.entities?.length) {
        setHighlightedNode(evt.entities[0]);
        setTimeout(() => setHighlightedNode(null), 2500);
      }

      // If action needs approval, push to pending
      if (evt.isPending && !pendingActions.find(a => a.id === evt.id)) {
        const newAction = {
          id: `ACT-LIVE-${Date.now()}`,
          type: 'FIREWALL_BLOCK',
          agent: evt.agent,
          target: evt.entities?.[0] || 'Unknown',
          asset: evt.entities?.[0] || 'Perimeter FW',
          risk: evt.reasoning || `Confidence ${evt.confidence}%`,
          severity: 'HIGH',
          action: 'Network Isolation',
          timestamp: new Date().toLocaleTimeString(),
          status: 'PENDING',
          description: `${evt.code || evt.content}`,
          impacted: evt.entities || [],
        };
        setPending(prev => [...prev, newAction]);
      }

      // Autonomy stats drift
      setAutonomy(prev => ({
        ...prev,
        agentActions: prev.agentActions + 1,
        level: Math.min(99, prev.level + (Math.random() > 0.7 ? 1 : 0)),
      }));

      // Agent tool count tick
      setAgents(prev => prev.map(a =>
        a.status === 'ACTIVE' && Math.random() > 0.6
          ? { ...a, tools: a.tools + 1 }
          : a
      ));
    };

    const id = setInterval(tick, 7000);

    // Initial fetch for investigations
    const fetchInvestigations = async () => {
      if (!token) return;
      try {
        const response = await fetch('http://localhost:8000/cases', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setInvestigations(data);
        }
      } catch (error) {
        console.error('Failed to fetch investigations:', error);
      }
    };
    fetchInvestigations();
    const invId = setInterval(fetchInvestigations, 30000);

    return () => {
      clearInterval(id);
      clearInterval(invId);
    };
  }, []);

  // ── Keyboard shortcut: Cmd/Ctrl + K ─────────────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdPaletteOpen(v => !v);
      }
      if (e.key === 'Escape') {
        setCmdPaletteOpen(false);
        setApprovalAction(null);
        setExplainEvent(null);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // ── Entity click handler ─────────────────────────────────────────────
  const clickEntity = useCallback((entityId) => {
    const entity = ENTITY_DB[entityId];
    if (!entity) return;
    setSelectedEntity(entity);
    setHighlightedNode(entityId);
    setEntityFilter(entityId);
    setTimeout(() => setHighlightedNode(null), 2500);
  }, []);

  const clearEntityFilter = useCallback(() => {
    setEntityFilter(null);
    setSelectedEntity(null);
  }, []);

  // ── Approval actions ─────────────────────────────────────────────────
  const approveAction = useCallback((actionId) => {
    setPending(prev => prev.filter(a => a.id !== actionId));
    setAutonomy(prev => ({ ...prev, humanApproved: prev.humanApproved + 1 }));
    setApprovalAction(null);
  }, []);

  const rejectAction = useCallback((actionId) => {
    setPending(prev => prev.filter(a => a.id !== actionId));
    setAutonomy(prev => ({ ...prev, humanOverrides: prev.humanOverrides + 1 }));
    setApprovalAction(null);
  }, []);

  return (
    <SOCContext.Provider value={{
      // Data
      agents, alerts, evidence, pendingActions, autonomy, timelineEvents,
      // Entity navigation
      selectedEntity, highlightedNode, entityFilter,
      clickEntity, clearEntityFilter,
      // Modals
      approvalAction, setApprovalAction,
      explainEvent, setExplainEvent,
      cmdPaletteOpen, setCmdPaletteOpen,
      // Replay
      replayProgress, setReplayProgress,
      replayPlaying, setReplayPlaying,
      // Actions
      approveAction, rejectAction,
      // Investigations
      investigations,
    }}>
      {children}
    </SOCContext.Provider>
  );
}

export const useSOC = () => {
  const ctx = useContext(SOCContext);
  if (!ctx) throw new Error('useSOC must be used within SOCProvider');
  return ctx;
};

import React, { useState } from 'react';
import { FileText, Braces, Activity, Package } from 'lucide-react';

const TABS = [
  { id: 'logs', label: 'Raw Logs', icon: FileText },
  { id: 'json', label: 'JSON View', icon: Braces },
  { id: 'telemetry', label: 'Telemetry', icon: Activity },
  { id: 'artifacts', label: 'Artifacts', icon: Package },
];

const LOG_CONTENT = `[14:02:10] INFO: Agent Sentinel-01 heartbeat received.
[14:02:11] TRAC: Hook detected on NtQuerySystemInformation.
[14:02:11] ALRT: MALICIOUS_PAYLOAD_DETECTED (Sig: 0x8823)

> Source: 192.168.1.105:53211
> Dest:   8.8.8.8:443
> Hash:   e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

CMD EXEC: whoami /all & systeminfo > C:\\Temp\\out.txt

[14:02:12] INFO: Isolation command dispatched.
[14:02:12] INFO: Firewall ruleset update ACK.
[14:02:14] SUCC: HOST-DX9 traffic blocked ingress/egress.
[14:02:14] INFO: Memory dump initiated (PID: 9912)
[14:02:19] SUCC: Dump complete. 3.2GB → /soc/reports/forensics/

[14:02:45] TRAC: HERALD-03 scanning adjacent subnet.
[14:02:45] INFO: 14 hosts found in 192.168.1.0/24
[14:02:46] ALRT: Suspicious SMB traffic from 192.168.1.108`;

const JSON_CONTENT = {
  incident_id: "INC-2023-981",
  severity: "CRITICAL",
  confidence: 0.94,
  mitre: ["T1059.001", "T1003", "T1021"],
  source_ip: "192.168.1.105",
  target: "Host-DX9",
  agent: "SENTINEL-01",
  status: "CONTAINED",
  timestamp: "2023-10-24T14:02:12Z"
};

const ARTIFACTS = [
  { name: 'HOST-DX9-memdump.dmp', size: '3.2 GB', type: 'Memory Dump', color: '#D84C7F' },
  { name: 'ps_payload.b64', size: '4.1 KB', type: 'Payload', color: '#EF4444' },
  { name: 'gap_analysis_INC-981.pdf', size: '1.8 MB', type: 'Report', color: '#88C057' },
  { name: 'network_pcap_1014.pcap', size: '22 MB', type: 'PCAP', color: '#3B6FE3' },
];

export default function EvidenceInspector() {
  const [activeTab, setActiveTab] = useState('logs');

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Tab Nav */}
      <div className="flex border-b flex-shrink-0" style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-all terminal`}
            style={{
              color: activeTab === id ? '#E2E8F0' : '#6B7280',
              borderBottom: activeTab === id ? '2px solid #3B6FE3' : '2px solid transparent',
            }}
          >
            <Icon size={11} />
            {label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-3">
        {activeTab === 'logs' && (
          <pre className="terminal text-xs whitespace-pre-wrap leading-relaxed"
            style={{ color: '#94A3B8' }}>
            {LOG_CONTENT.split('\n').map((line, i) => {
              const isAlert = line.includes('ALRT');
              const isSuccess = line.includes('SUCC');
              const isTrace = line.includes('TRAC') || line.startsWith('>');
              const color = isAlert ? '#EF4444' : isSuccess ? '#88C057' : isTrace ? '#D84C7F' : '#6B7280';
              return <span key={i} style={{ color }} className="block">{line}</span>;
            })}
          </pre>
        )}

        {activeTab === 'json' && (
          <pre className="terminal text-xs" style={{ color: '#94A3B8' }}>
            {JSON.stringify(JSON_CONTENT, null, 2).split('\n').map((line, i) => {
              const isKey = line.includes('"') && line.includes(':');
              const isValue = line.trim().startsWith('"');
              const isCritical = line.includes('CRITICAL') || line.includes('SENTINEL');
              const color = isCritical ? '#EF4444' : isKey ? '#93C5FD' : '#88C057';
              return <span key={i} style={{ color }} className="block">{line}</span>;
            })}
          </pre>
        )}

        {activeTab === 'telemetry' && (
          <div className="space-y-2 text-xs terminal">
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Events/sec', value: '14.2k', color: '#EF4444' },
                { label: 'Agents Active', value: '12/12', color: '#88C057' },
                { label: 'Hypothesis Confidence', value: '94%', color: '#D84C7F' },
                { label: 'Isolation Status', value: 'CONFIRMED', color: '#88C057' },
                { label: 'Memory Dump', value: '3.2 GB', color: '#3B6FE3' },
                { label: 'MITRE TTPs Hit', value: '3', color: '#E5A862' },
              ].map(({ label, value, color }) => (
                <div key={label} className="rounded p-2" style={{ background: '#111827', border: '1px solid #1F2937' }}>
                  <p style={{ color: '#6B7280' }}>{label}</p>
                  <p className="text-base font-bold mt-0.5" style={{ color }}>{value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'artifacts' && (
          <div className="space-y-2">
            {ARTIFACTS.map(a => (
              <div key={a.name} className="flex items-center gap-3 p-2 rounded cursor-pointer hover:brightness-125 transition-all"
                style={{ background: '#111827', border: '1px solid #1F2937' }}>
                <div className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0"
                  style={{ background: `${a.color}22`, border: `1px solid ${a.color}` }}>
                  <Package size={12} style={{ color: a.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs terminal truncate" style={{ color: '#CBD5E1' }}>{a.name}</p>
                  <p className="text-xs" style={{ color: '#6B7280' }}>{a.type} · {a.size}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

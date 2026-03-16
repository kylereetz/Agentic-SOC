import React, { useState } from 'react';
import { AlertTriangle, Filter, Search, ChevronUp, ChevronDown, Zap, Clock, Server, Shield } from 'lucide-react';

const SEVERITIES = ['Critical', 'High', 'Medium', 'Low'];
const SOURCES = ['All', 'EDR', 'SIEM', 'IDS', 'SOAR'];
const TIME_RANGES = ['Last 1h', 'Last 6h', 'Last 24h', '7 Days'];

const SEVERITY_STYLES = {
  Critical: { bg: '#EF444422', border: '#EF4444', color: '#EF4444' },
  High:     { bg: '#E5A86222', border: '#E5A862', color: '#E5A862' },
  Medium:   { bg: '#3B6FE322', border: '#3B6FE3', color: '#3B6FE3' },
  Low:      { bg: '#88C05722', border: '#88C057', color: '#88C057' },
};

const ALERTS = [
  { id: 'ALT-001', severity: 'Critical', source: 'EDR', asset: 'Host-DX9', time: '14:02:11', mitre: 'T1059.001', agent: 'SENTINEL-01', title: 'Malicious PowerShell Execution' },
  { id: 'ALT-002', severity: 'Critical', source: 'SIEM', asset: '192.168.1.105', time: '14:01:55', mitre: 'T1003', agent: 'HERALD-03', title: 'Credential Dumping via LSASS' },
  { id: 'ALT-003', severity: 'High', source: 'IDS', asset: 'Host-WS4', time: '13:58:22', mitre: 'T1021', agent: 'RECON-02', title: 'SMB Lateral Movement' },
  { id: 'ALT-004', severity: 'High', source: 'EDR', asset: 'srv-dc01', time: '13:55:14', mitre: 'T1558.003', agent: 'HERALD-03', title: 'Kerberoasting Attempt' },
  { id: 'ALT-005', severity: 'Medium', source: 'SIEM', asset: '10.0.0.22', time: '13:50:02', mitre: 'T1071.001', agent: 'UNASSIGNED', title: 'Abnormal DNS Tunneling' },
  { id: 'ALT-006', severity: 'Medium', source: 'IDS', asset: 'wks-kyler', time: '13:44:30', mitre: 'T1078', agent: 'SENTINEL-01', title: 'Valid Account Abuse' },
  { id: 'ALT-007', severity: 'Critical', source: 'EDR', asset: 'Host-DX9', time: '13:40:01', mitre: 'T1055', agent: 'SENTINEL-01', title: 'Process Injection Detected' },
  { id: 'ALT-008', severity: 'Low', source: 'SOAR', asset: 'OT-PLC-01', time: '13:22:17', mitre: 'T1046', agent: 'UNASSIGNED', title: 'Non-standard Modbus Write' },
];

function SeverityBadge({ level }) {
  const s = SEVERITY_STYLES[level] || SEVERITY_STYLES['Low'];
  return (
    <span className="inline-flex items-center gap-1 text-xs font-bold terminal px-2 py-0.5 rounded"
      style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.color }}>
      {level === 'Critical' && <span className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: s.color }} />}
      {level}
    </span>
  );
}

export default function AlertQueue() {
  const [activeSev, setActiveSev] = useState('All');
  const [activeSource, setActiveSource] = useState('All');
  const [timeRange, setTimeRange] = useState('Last 6h');
  const [search, setSearch] = useState('');
  const [sortDir, setSortDir] = useState('desc');
  const [selectedAlert, setSelectedAlert] = useState(null);

  const filtered = ALERTS.filter(a =>
    (activeSev === 'All' || a.severity === activeSev) &&
    (activeSource === 'All' || a.source === activeSource) &&
    (!search || a.title.toLowerCase().includes(search.toLowerCase()) || a.asset.includes(search))
  );

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <AlertTriangle size={15} style={{ color: '#EF4444' }} />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>ALERT QUEUE</span>
        <span className="ml-1 text-xs terminal px-2 py-0.5 rounded-full"
          style={{ background: '#EF444422', color: '#EF4444', border: '1px solid #EF444444' }}>
          {filtered.length}
        </span>

        <div className="flex-1 relative ml-4">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: '#4B5563' }} />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search alerts, hosts, IPs..."
            className="w-full text-xs py-1.5 pl-8 pr-3 rounded terminal focus:outline-none"
            style={{ background: '#111827', border: '1px solid #1F2937', color: '#9CA3AF' }} />
        </div>

        {/* Time Range */}
        <div className="flex items-center gap-1">
          {TIME_RANGES.map(t => (
            <button key={t} onClick={() => setTimeRange(t)}
              className="text-xs terminal px-2.5 py-1 rounded transition-all"
              style={{
                background: timeRange === t ? '#3B6FE322' : 'transparent',
                color: timeRange === t ? '#3B6FE3' : '#6B7280',
                border: `1px solid ${timeRange === t ? '#3B6FE344' : 'transparent'}`
              }}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Filter Row */}
      <div className="flex items-center gap-2 px-4 py-2 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937' }}>
        <Filter size={11} style={{ color: '#6B7280' }} />
        <span className="text-xs" style={{ color: '#6B7280' }}>Severity:</span>
        {['All', ...SEVERITIES].map(s => {
          const style = s !== 'All' ? SEVERITY_STYLES[s] : null;
          return (
            <button key={s} onClick={() => setActiveSev(s)}
              className="text-xs terminal px-2 py-0.5 rounded-full transition-all"
              style={{
                background: activeSev === s ? (style?.bg || '#FFFFFF11') : 'transparent',
                color: activeSev === s ? (style?.color || '#E2E8F0') : '#6B7280',
                border: `1px solid ${activeSev === s ? (style?.border || '#6B7280') : 'transparent'}`,
              }}>
              {s}
            </button>
          );
        })}
        <div className="w-px h-4 mx-2" style={{ background: '#1F2937' }} />
        <span className="text-xs" style={{ color: '#6B7280' }}>Source:</span>
        {SOURCES.map(s => (
          <button key={s} onClick={() => setActiveSource(s)}
            className="text-xs terminal px-2 py-0.5 rounded transition-all"
            style={{
              background: activeSource === s ? '#FFFFFF11' : 'transparent',
              color: activeSource === s ? '#E2E8F0' : '#6B7280',
              border: `1px solid ${activeSource === s ? '#374151' : 'transparent'}`,
            }}>
            {s}
          </button>
        ))}
      </div>

      {/* Table Header */}
      <div className="grid text-xs terminal px-4 py-2 border-b flex-shrink-0"
        style={{ gridTemplateColumns: '100px 1fr 120px 80px 110px 130px 130px', borderColor: '#1F2937', color: '#4B5563' }}>
        <span>SEVERITY</span>
        <span>ALERT</span>
        <span>ASSET</span>
        <span>SOURCE</span>
        <div className="flex items-center gap-1 cursor-pointer" onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')}>
          TIME {sortDir === 'asc' ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
        </div>
        <span>MITRE ATT&CK</span>
        <span>AGENT</span>
      </div>

      {/* Table Rows */}
      <div className="flex-1 overflow-y-auto">
        {filtered.map(alert => {
          const s = SEVERITY_STYLES[alert.severity];
          const isCritical = alert.severity === 'Critical';
          return (
            <div key={alert.id}
              onClick={() => setSelectedAlert(selectedAlert?.id === alert.id ? null : alert)}
              className="grid items-center px-4 py-2.5 border-b cursor-pointer hover:brightness-125 transition-all"
              style={{
                gridTemplateColumns: '100px 1fr 120px 80px 110px 130px 130px',
                borderColor: '#1F2937',
                background: selectedAlert?.id === alert.id ? '#111827' : isCritical ? 'rgba(239,68,68,0.03)' : 'transparent',
                borderLeft: isCritical ? `2px solid #EF4444` : '2px solid transparent',
              }}>
              <span><SeverityBadge level={alert.severity} /></span>
              <span className="text-xs" style={{ color: '#CBD5E1' }}>{alert.title}</span>
              <span className="text-xs terminal" style={{ color: '#93C5FD' }}>{alert.asset}</span>
              <span className="text-xs terminal" style={{ color: '#6B7280' }}>{alert.source}</span>
              <span className="text-xs terminal" style={{ color: '#6B7280' }}>{alert.time}</span>
              <span className="text-xs terminal px-2 py-0.5 rounded"
                style={{ background: '#D84C7F11', color: '#D84C7F', border: '1px solid #D84C7F22', width: 'fit-content' }}>
                {alert.mitre}
              </span>
              <div className="flex items-center gap-2">
                {alert.agent !== 'UNASSIGNED'
                  ? <span className="text-xs terminal" style={{ color: '#3B6FE3' }}>{alert.agent}</span>
                  : <span className="text-xs terminal" style={{ color: '#4B5563' }}>—</span>
                }
              </div>
            </div>
          );
        })}
      </div>

      {/* Expanded Alert Actions */}
      {selectedAlert && (
        <div className="border-t px-4 py-3 flex-shrink-0 flex items-center gap-3"
          style={{ borderColor: `${SEVERITY_STYLES[selectedAlert.severity].border}55`, background: '#111827' }}>
          <div className="flex-1 text-xs" style={{ color: '#9CA3AF' }}>
            <span className="font-bold" style={{ color: '#E2E8F0' }}>{selectedAlert.id}</span>
            {' — '}{selectedAlert.title}
          </div>
          <button className="text-xs terminal px-3 py-1.5 rounded transition-all hover:brightness-125"
            style={{ background: '#3B6FE322', color: '#3B6FE3', border: '1px solid #3B6FE344' }}>
            Assign Agent
          </button>
          <button className="text-xs terminal px-3 py-1.5 rounded transition-all hover:brightness-125"
            style={{ background: '#D84C7F22', color: '#D84C7F', border: '1px solid #D84C7F44' }}>
            Promote to Investigation
          </button>
        </div>
      )}
    </div>
  );
}

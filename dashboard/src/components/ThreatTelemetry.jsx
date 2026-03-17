import React, { useState, useEffect } from 'react';
import { DollarSign, AlertTriangle, Skull, TrendingUp, Clock, ShieldOff } from 'lucide-react';

// ── Mock Data ─────────────────────────────────────────────────────────────────
const DECEPTION_ALERTS = [
  {
    id: 'MIRAGE-001',
    decoy: 'PLC-SIEM-FAKE-01 (Siemens S7-1500)',
    src_ip: '10.0.44.82',
    action: 'Modbus Read — address 0x0100, qty 64',
    timestamp: '22:34:02',
    severity: 'CRITICAL',
  },
  {
    id: 'MIRAGE-002',
    decoy: 'CAD Share: \\\\files01\\NDA_CONTRACTS_2026',
    src_ip: '10.0.44.83',
    action: 'SMB OPEN — DCA_Proposal_FINAL.pdf',
    timestamp: '22:34:49',
    severity: 'CRITICAL',
  },
];

const RISK_INCIDENTS = [
  {
    id: 'INC-2026-041', title: 'Active Lateral Movement — COBALT STRIKE',
    asset: 'DC-01', source: 'SENTINEL-CORRELATOR',
    loss_per_hr: 88400, likelihood: 0.97, severity: 'Critical',
    mitre: 'T1021', time: '22:14:11',
  },
  {
    id: 'INC-2026-039', title: 'Ransomware Precursor — Shadow Copy Delete',
    asset: 'MFG-PROD-01', source: 'SENTINEL-TRIAGE',
    loss_per_hr: 62000, likelihood: 0.88, severity: 'Critical',
    mitre: 'T1490', time: '21:58:33',
  },
  {
    id: 'INC-2026-040', title: 'Cloud IAM Escalation — Admin Policy Attach',
    asset: 'AWS-Account', source: 'SENTINEL-CLOUD-WRAITH',
    loss_per_hr: 44100, likelihood: 0.91, severity: 'Critical',
    mitre: 'T1548.005', time: '22:01:07',
  },
  {
    id: 'INC-2026-037', title: 'Supply Chain: Log4Shell in MFG Dependency',
    asset: 'MFG-WS-01', source: 'SENTINEL-VANGUARD',
    loss_per_hr: 31200, likelihood: 0.75, severity: 'High',
    mitre: 'CVE-2021-44228', time: '21:42:55',
  },
  {
    id: 'INC-2026-038', title: 'MFA Fatigue Attack — jdoe Account',
    asset: 'AD-Controller', source: 'SENTINEL-GATEKEEPER',
    loss_per_hr: 18700, likelihood: 0.82, severity: 'High',
    mitre: 'T1621', time: '21:50:14',
  },
  {
    id: 'INC-2026-035', title: 'DNS Tunneling — Suspicious Beacon',
    asset: '10.0.0.22', source: 'SENTINEL-TRAFFIC-SIEVE',
    loss_per_hr: 5200, likelihood: 0.59, severity: 'Medium',
    mitre: 'T1071.004', time: '21:22:30',
  },
];

const SEV_STYLES = {
  Critical: { color: '#EF4444', bg: '#EF444418', border: '#EF444433' },
  High:     { color: '#E5A862', bg: '#E5A86218', border: '#E5A86233' },
  Medium:   { color: '#3B6FE3', bg: '#3B6FE318', border: '#3B6FE333' },
  Low:      { color: '#88C057', bg: '#88C05718', border: '#88C05733' },
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function DeceptionBanner({ alert }) {
  return (
    <div className="rounded-xl p-4 mb-3 animate-pulse-magenta neon-border"
      style={{
        background: '#D84C7F0C',
        border: '1px solid #D84C7F66',
      }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Skull size={16} style={{ color: '#D84C7F' }} className="animate-blink" />
          <span className="text-xs font-bold terminal tracking-widest" style={{ color: '#D84C7F' }}>
            SENTINEL-MIRAGE DECEPTION HIT
          </span>
          <span className="text-xs terminal px-2 py-0.5 rounded-full font-bold"
            style={{ background: '#EF444422', color: '#EF4444', border: '1px solid #EF444444' }}>
            ⚡ BYPASS TRIAGE QUEUE
          </span>
        </div>
        <span className="text-xs terminal" style={{ color: '#6B7280' }}>{alert.timestamp}</span>
      </div>

      {/* Body */}
      <div className="grid grid-cols-3 gap-3 text-xs terminal">
        <div>
          <p style={{ color: '#4B5563' }}>DECOY ASSET</p>
          <p className="mt-0.5 font-bold" style={{ color: '#E2E8F0' }}>{alert.decoy}</p>
        </div>
        <div>
          <p style={{ color: '#4B5563' }}>SOURCE IP</p>
          <p className="mt-0.5 font-bold" style={{ color: '#EF4444' }}>{alert.src_ip}</p>
        </div>
        <div>
          <p style={{ color: '#4B5563' }}>ACTION</p>
          <p className="mt-0.5" style={{ color: '#E5A862' }}>{alert.action}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <button className="text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all action-btn"
          style={{ background: '#EF444422', color: '#EF4444', border: '1px solid #EF444433' }}>
          🔒 Isolate Immediately
        </button>
        <button className="text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
          style={{ background: '#D84C7F22', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
          → Open Investigation
        </button>
        <span className="ml-auto text-xs terminal" style={{ color: '#4B5563' }}>{alert.id}</span>
      </div>
    </div>
  );
}

function LossMagnitudeBar({ value, max }) {
  const pct = Math.min((value / max) * 100, 100);
  const color = pct > 80 ? '#EF4444' : pct > 50 ? '#E5A862' : '#3B6FE3';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: '#1F2937' }}>
        <div className="h-full rounded-full progress-bar" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-xs terminal font-bold flex-shrink-0" style={{ color, minWidth: 70 }}>
        ${value.toLocaleString()}/hr
      </span>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function ThreatTelemetry() {
  const [incidents] = useState(RISK_INCIDENTS.sort((a, b) => b.loss_per_hr - a.loss_per_hr));
  const [deceptionAlerts, setDeceptionAlerts] = useState(DECEPTION_ALERTS);
  const [selectedInc, setSelectedInc] = useState(null);
  const maxLoss = incidents[0]?.loss_per_hr || 1;

  const totalExposure = incidents.reduce((s, i) => s + i.loss_per_hr * i.likelihood, 0);

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <TrendingUp size={14} style={{ color: '#EF4444' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            THREAT TELEMETRY
          </span>
          <span className="text-xs terminal" style={{ color: '#6B7280' }}>
            sorted by Loss Magnitude (SENTINEL-RISK-QUANTIFIER)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <DollarSign size={12} style={{ color: '#E5A862' }} />
          <span className="text-sm font-bold terminal" style={{ color: '#E5A862' }}>
            ${Math.round(totalExposure).toLocaleString()}/hr
          </span>
          <span className="text-xs terminal" style={{ color: '#4B5563' }}>total exposure</span>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* LEFT: Risk-Quantified Incident Queue */}
        <div className="flex flex-col" style={{ flex: '1 1 60%', borderRight: '1px solid #1F2937' }}>
          {/* Column headers */}
          <div className="grid text-xs terminal px-4 py-2 border-b flex-shrink-0"
            style={{ gridTemplateColumns: '80px 1fr 110px 100px', borderColor: '#1F2937', color: '#4B5563' }}>
            <span>SEV</span>
            <span>INCIDENT</span>
            <span>MITRE</span>
            <span>LOSS/HR</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            {incidents.map((inc, i) => {
              const s = SEV_STYLES[inc.severity] || SEV_STYLES.Low;
              const isSelected = selectedInc?.id === inc.id;
              const rank = i + 1;
              return (
                <div key={inc.id}
                  onClick={() => setSelectedInc(isSelected ? null : inc)}
                  className="cursor-pointer hover:brightness-125 transition-all"
                  style={{
                    borderBottom: '1px solid #1F2937',
                    background: isSelected ? '#111827' : rank === 1 ? '#EF444406' : 'transparent',
                    borderLeft: rank <= 3 ? `2px solid ${s.color}` : '2px solid transparent',
                  }}>

                  {/* Main Row */}
                  <div className="grid items-center px-4 py-3"
                    style={{ gridTemplateColumns: '80px 1fr 110px 100px' }}>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs terminal font-bold opacity-30" style={{ minWidth: 16 }}>
                        #{rank}
                      </span>
                      <span className="text-xs terminal font-bold px-1.5 py-0.5 rounded"
                        style={{ background: s.bg, color: s.color, border: `1px solid ${s.border}` }}>
                        {inc.severity}
                      </span>
                    </div>
                    <div>
                      <p className="text-xs font-medium" style={{ color: '#CBD5E1' }}>{inc.title}</p>
                      <p className="text-xs terminal mt-0.5" style={{ color: '#4B5563' }}>
                        {inc.asset} · {inc.source} · {inc.time}
                      </p>
                    </div>
                    <span className="text-xs terminal px-2 py-0.5 rounded"
                      style={{ background: '#D84C7F11', color: '#D84C7F', border: '1px solid #D84C7F22', width: 'fit-content' }}>
                      {inc.mitre}
                    </span>
                    <LossMagnitudeBar value={inc.loss_per_hr} max={maxLoss} />
                  </div>

                  {/* Expanded detail */}
                  {isSelected && (
                    <div className="px-4 pb-3 border-t" style={{ borderColor: '#1F2937' }}>
                      <div className="flex items-center gap-3 mt-2">
                        <div className="flex-1 text-xs terminal" style={{ color: '#6B7280', lineHeight: 1.6 }}>
                          <span style={{ color: '#9CA3AF' }}>Likelihood: </span>
                          <span style={{ color: s.color }}>{Math.round(inc.likelihood * 100)}%</span>
                          <span className="mx-2">·</span>
                          <span style={{ color: '#9CA3AF' }}>Expected Loss: </span>
                          <span style={{ color: '#E5A862' }}>
                            ${Math.round(inc.loss_per_hr * inc.likelihood).toLocaleString()}/hr
                          </span>
                        </div>
                        <button className="text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
                          style={{ background: '#3B6FE322', color: '#3B6FE3', border: '1px solid #3B6FE333' }}>
                          Open Case
                        </button>
                        <button className="text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
                          style={{ background: '#D84C7F22', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
                          Assign Agent
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT: Deception Alerts */}
        <div className="flex flex-col overflow-y-auto" style={{ flex: '1 1 40%' }}>
          <div className="flex items-center gap-2 px-4 py-3 border-b flex-shrink-0"
            style={{ borderColor: '#1F2937' }}>
            <Skull size={12} style={{ color: '#D84C7F' }} className="animate-blink" />
            <span className="text-xs terminal font-bold" style={{ color: '#D84C7F' }}>
              DECEPTION ALERTS
            </span>
            <span className="ml-auto text-xs terminal px-2 py-0.5 rounded-full"
              style={{ background: '#D84C7F20', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
              {deceptionAlerts.length} HIT{deceptionAlerts.length !== 1 ? 'S' : ''}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {deceptionAlerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 gap-2">
                <ShieldOff size={24} style={{ color: '#1F2937' }} />
                <p className="text-xs terminal" style={{ color: '#374151' }}>No active deception hits</p>
              </div>
            ) : (
              deceptionAlerts.map(a => <DeceptionBanner key={a.id} alert={a} />)
            )}

            {/* Explanation card */}
            <div className="rounded-lg p-3 mt-1"
              style={{ background: '#111827', border: '1px solid #1F2937' }}>
              <p className="text-xs terminal" style={{ color: '#4B5563', lineHeight: 1.7 }}>
                SENTINEL-MIRAGE deploys silent decoy assets across the OT environment.
                Any interaction with a decoy is a <span style={{ color: '#D84C7F' }}>zero-false-positive</span> signal —
                legitimate users never touch fake PLCs or honeypot shares.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

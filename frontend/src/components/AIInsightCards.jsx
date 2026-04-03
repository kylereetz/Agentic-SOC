import React, { useState } from 'react';
import { Lightbulb, AlertTriangle, ArrowRight, X, ChevronDown, ChevronUp } from 'lucide-react';

const INSIGHTS = [
  {
    id: 'I1',
    severity: 'Critical',
    color: '#EF4444',
    title: 'Possible credential compromise detected',
    summary: 'SENTINEL-01 has identified a high-confidence credential theft chain matching APT-29 TTPs.',
    evidence: [
      'Suspicious PowerShell execution with base64 payload (Host-DX9)',
      'LSASS memory read — likely Mimikatz or equivalent (PID 9912)',
      'Lateral movement attempt via SMB (3 hops detected)',
    ],
    action: 'Immediately isolate Host-DX9 and review all domain admin sessions.',
    mitre: 'T1003 | T1021 | T1059.001',
  },
  {
    id: 'I2',
    severity: 'High',
    color: '#E5A862',
    title: 'DNS tunneling exfiltration suspected',
    summary: 'Anomalous DNS query volume from 10.0.0.22 to external resolver. Pattern matches DNS tunneling tools.',
    evidence: [
      'Query rate 450 req/min (baseline: 12)',
      'TXT record payloads contain Base64 chunks',
      'Destination: rare TLD (.info) with < 7 day registration',
    ],
    action: 'Block outbound DNS to non-corporate resolvers. Capture full DNS payload.',
    mitre: 'T1071.004',
  },
  {
    id: 'I3',
    severity: 'Medium',
    color: '#3B6FE3',
    title: 'Kerberoasting attempt identified',
    summary: 'Multiple TGS requests for service accounts in a short window. Classic offline password cracking setup.',
    evidence: [
      'KR\\svc_sql: 4 TGS requests in 8 seconds',
      'Requesting host: Host-WS4 (not typical behavior)',
      'RC4 encryption downgrade requested',
    ],
    action: 'Enforce AES-only Kerberos. Reset service account passwords.',
    mitre: 'T1558.003',
  },
];

const SEV_STYLES = {
  Critical: { bg: '#EF444411', border: '#EF444433', color: '#EF4444' },
  High:     { bg: '#E5A86211', border: '#E5A86233', color: '#E5A862' },
  Medium:   { bg: '#3B6FE311', border: '#3B6FE333', color: '#3B6FE3' },
};

function InsightCard({ insight }) {
  const [expanded, setExpanded] = useState(false);
  const st = SEV_STYLES[insight.severity];

  return (
    <div className="rounded-lg overflow-hidden animate-slide-in"
      style={{ background: '#111827', border: `1px solid ${st.border}` }}>
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
          style={{ background: st.bg, border: `1px solid ${st.border}` }}>
          <Lightbulb size={12} style={{ color: insight.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs terminal px-1.5 py-0.5 rounded"
              style={{ background: st.bg, color: insight.color, border: `1px solid ${st.border}` }}>
              {insight.severity}
            </span>
            <span className="text-xs terminal" style={{ color: '#4B5563' }}>{insight.mitre}</span>
          </div>
          <p className="text-sm font-semibold" style={{ color: '#E2E8F0' }}>{insight.title}</p>
          <p className="text-xs mt-1 leading-relaxed" style={{ color: '#9CA3AF' }}>{insight.summary}</p>
        </div>
        <button onClick={() => setExpanded(v => !v)}
          className="hover:opacity-70 transition-opacity flex-shrink-0 mt-1">
          {expanded ? <ChevronUp size={14} style={{ color: '#6B7280' }} /> : <ChevronDown size={14} style={{ color: '#6B7280' }} />}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t space-y-3" style={{ borderColor: '#1F2937' }}>
          <div className="mt-3">
            <p className="text-xs terminal font-bold mb-2" style={{ color: '#6B7280' }}>EVIDENCE</p>
            <ul className="space-y-1.5">
              {insight.evidence.map((e, i) => (
                <li key={i} className="flex items-start gap-2 text-xs" style={{ color: '#CBD5E1' }}>
                  <span className="flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center"
                    style={{ background: st.bg, color: insight.color, fontSize: 9 }}>{i + 1}</span>
                  {e}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded p-3" style={{ background: '#0B1117', border: `1px solid ${st.border}` }}>
            <p className="text-xs terminal font-bold mb-1" style={{ color: insight.color }}>RECOMMENDED ACTION</p>
            <p className="text-xs" style={{ color: '#CBD5E1' }}>{insight.action}</p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-1.5 text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
              style={{ background: `${insight.color}18`, color: insight.color, border: `1px solid ${insight.color}33` }}>
              Act Now <ArrowRight size={11} />
            </button>
            <button className="flex items-center gap-1.5 text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
              style={{ background: '#FFFFFF08', color: '#6B7280', border: '1px solid #1F2937' }}>
              <X size={11} /> Dismiss
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AIInsightCards() {
  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      <div className="flex items-center gap-2 px-4 py-2.5 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <Lightbulb size={13} style={{ color: '#E5A862' }} className="animate-pulse" />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>AI INSIGHT CARDS</span>
        <span className="ml-auto text-xs terminal px-2 py-0.5 rounded-full"
          style={{ background: '#E5A86222', color: '#E5A862', border: '1px solid #E5A86244' }}>
          {INSIGHTS.length} new
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {INSIGHTS.map(i => <InsightCard key={i.id} insight={i} />)}
      </div>
    </div>
  );
}

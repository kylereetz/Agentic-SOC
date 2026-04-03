import React, { useState } from 'react';
import { Target, TrendingUp, TrendingDown, ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';

const HYPOTHESES = [
  {
    id: 'H1',
    title: 'Credential Theft via Spear Phishing',
    description: 'Attacker used targeted phishing to compromise a service account with domain admin privileges. Initial access vector: email attachment with macro payload.',
    confidence: 89,
    supporting: ['PowerShell base64 execution', 'LSASS memory read (PID 9912)', 'Suspicious Outlook process tree'],
    against: ['No phishing email found in Exchange logs'],
  },
  {
    id: 'H2',
    title: 'Insider Threat — Privileged User',
    description: 'A legitimate domain admin account is being used maliciously. Account: KR\\admin. Activity pattern matches after-hours exfiltration behavior.',
    confidence: 64,
    supporting: ['Off-hours logon at 02:14 AM', 'Large data transfer to external IP'],
    against: ['No HR anomalies flagged', 'User-agent signature is normal'],
  },
  {
    id: 'H3',
    title: 'Supply Chain Compromise',
    description: 'A legitimate software update may contain a backdoor. Update agent svchost.exe variant shows anomalous behavior not matching known-good baseline.',
    confidence: 31,
    supporting: ['Modified svchost.exe timestamp'],
    against: ['Software vendor confirmed build integrity', 'Hash matches signed release'],
  },
];

function ConfidenceMeter({ value }) {
  const color = value >= 75 ? '#EF4444' : value >= 50 ? '#E5A862' : '#88C057';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: '#1F2937' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-xs font-bold terminal" style={{ color, minWidth: 36 }}>{value}%</span>
    </div>
  );
}

export default function HypothesisPanel() {
  const [expanded, setExpanded] = useState('H1');

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      <div className="flex items-center gap-2 px-4 py-2.5 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <Target size={13} style={{ color: '#EF4444' }} />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>AI HYPOTHESES</span>
        <span className="ml-auto text-xs terminal" style={{ color: '#6B7280' }}>{HYPOTHESES.length} active</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {HYPOTHESES.map(h => {
          const isOpen = expanded === h.id;
          const color = h.confidence >= 75 ? '#EF4444' : h.confidence >= 50 ? '#E5A862' : '#6B7280';
          return (
            <div key={h.id}
              className="rounded-lg overflow-hidden transition-all"
              style={{ background: '#111827', border: `1px solid ${isOpen ? color + '44' : '#1F2937'}` }}>
              {/* Header */}
              <button
                onClick={() => setExpanded(isOpen ? null : h.id)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:brightness-110 transition-all">
                <div className="flex-1">
                  <p className="text-xs font-semibold" style={{ color: '#E2E8F0' }}>{h.title}</p>
                  <div className="mt-1.5">
                    <ConfidenceMeter value={h.confidence} />
                  </div>
                </div>
                {isOpen ? <ChevronUp size={14} style={{ color: '#6B7280' }} /> : <ChevronDown size={14} style={{ color: '#6B7280' }} />}
              </button>

              {/* Expanded */}
              {isOpen && (
                <div className="px-4 pb-4 space-y-3 border-t" style={{ borderColor: '#1F2937' }}>
                  <p className="text-xs mt-3 leading-relaxed" style={{ color: '#9CA3AF' }}>{h.description}</p>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <div className="flex items-center gap-1.5 mb-2">
                        <TrendingUp size={11} style={{ color: '#88C057' }} />
                        <span className="terminal font-bold" style={{ color: '#88C057' }}>Supporting</span>
                      </div>
                      <ul className="space-y-1">
                        {h.supporting.map((s, i) => (
                          <li key={i} className="flex items-start gap-1.5" style={{ color: '#9CA3AF' }}>
                            <span style={{ color: '#88C057', flexShrink: 0 }}>+</span> {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5 mb-2">
                        <TrendingDown size={11} style={{ color: '#EF4444' }} />
                        <span className="terminal font-bold" style={{ color: '#EF4444' }}>Contradicting</span>
                      </div>
                      <ul className="space-y-1">
                        {h.against.map((s, i) => (
                          <li key={i} className="flex items-start gap-1.5" style={{ color: '#9CA3AF' }}>
                            <span style={{ color: '#EF4444', flexShrink: 0 }}>−</span> {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-1">
                    <button className="flex-1 text-xs terminal py-1.5 rounded hover:brightness-125 transition-all"
                      style={{ background: '#3B6FE322', color: '#3B6FE3', border: '1px solid #3B6FE333' }}>
                      Promote to Primary
                    </button>
                    <button className="text-xs terminal px-3 py-1.5 rounded hover:brightness-125 transition-all"
                      style={{ background: '#EF444420', color: '#EF4444', border: '1px solid #EF444433' }}>
                      Dismiss
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

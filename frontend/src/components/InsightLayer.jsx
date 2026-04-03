import React from 'react';
import { Target, Lightbulb, BookOpen, TrendingUp, ChevronRight } from 'lucide-react';

const INSIGHTS = [
  {
    id: 'hypothesis',
    title: 'ACTIVE HYPOTHESIS',
    icon: Target,
    color: '#EF4444',
    badge: 'CONFIDENCE: 89%',
    badgeColor: '#EF4444',
    content: 'Probable lateral movement via compromised Service Account. Attacker is likely targeting the Domain Controller using Silver Ticket attack.',
    actions: null,
  },
  {
    id: 'insight',
    title: 'AI INSIGHT',
    icon: Lightbulb,
    color: '#3B6FE3',
    badge: null,
    content: 'Pattern matches "APT-29" TTPs observed in Q3 campaign. 14 related IOCs found in internal threat intelligence database.',
    actions: ['VIEW SIMILAR INCIDENTS (3)', 'EXPORT IOC LIST'],
  },
  {
    id: 'story',
    title: 'ATTACK STORY',
    icon: BookOpen,
    color: '#D84C7F',
    badge: null,
    content: null,
    steps: [
      { label: 'Initial Access', detail: 'Phishing (Credential Harvest)', done: true },
      { label: 'Persistence', detail: 'WMI Event Consumer', done: true },
      { label: 'Lateral Movement', detail: 'SMB / Pass-the-Hash', done: true },
      { label: 'Exfiltration', detail: 'DNS Tunneling', inProgress: true },
    ],
  },
];

export default function InsightLayer() {
  return (
    <div className="flex gap-2 h-full p-2 overflow-x-auto">
      {INSIGHTS.map(item => {
        const Icon = item.icon;
        return (
          <div key={item.id} className="flex-1 min-w-[220px] rounded-lg flex flex-col overflow-hidden"
            style={{ background: '#111827', border: `1px solid ${item.color}33` }}>
            {/* Card Header */}
            <div className="flex items-center justify-between px-3 py-2 border-b"
              style={{ borderColor: `${item.color}33` }}>
              <div className="flex items-center gap-2">
                <Icon size={13} style={{ color: item.color }} />
                <span className="text-xs font-bold tracking-widest terminal" style={{ color: item.color }}>
                  {item.title}
                </span>
              </div>
              {item.badge && (
                <span className="text-xs terminal px-2 py-0.5 rounded glow-red"
                  style={{
                    background: `${item.badgeColor}22`,
                    color: item.badgeColor,
                    border: `1px solid ${item.badgeColor}44`,
                  }}>
                  {item.badge}
                </span>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 px-3 py-2 overflow-y-auto">
              {item.content && (
                <p className="text-xs leading-relaxed" style={{ color: '#CBD5E1' }}>{item.content}</p>
              )}

              {item.steps && (
                <div className="space-y-1.5 mt-1">
                  {item.steps.map((step, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <ChevronRight size={11}
                        style={{ color: step.inProgress ? '#E5A862' : step.done ? '#88C057' : '#4B5563', marginTop: 2, flexShrink: 0 }} />
                      <div>
                        <span style={{ color: step.inProgress ? '#E5A862' : step.done ? '#CBD5E1' : '#6B7280' }}>
                          {step.label}:&nbsp;
                        </span>
                        <span className="terminal" style={{ color: '#6B7280' }}>{step.detail}</span>
                        {step.inProgress && (
                          <span className="ml-2 text-xs animate-blink" style={{ color: '#E5A862' }}>[IN PROGRESS]</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            {item.actions && (
              <div className="flex flex-wrap gap-1.5 px-3 pb-2">
                {item.actions.map(action => (
                  <button key={action}
                    className="text-xs terminal px-2 py-1 rounded hover:brightness-125 transition-all"
                    style={{ color: item.color, background: `${item.color}11`, border: `1px solid ${item.color}33` }}>
                    {action}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

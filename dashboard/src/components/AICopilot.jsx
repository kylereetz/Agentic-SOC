import React, { useState, useRef, useEffect } from 'react';
import { Send, X, Bot, User, Sparkles } from 'lucide-react';

const SUGGESTIONS = [
  'How did the attacker gain access?',
  'Show suspicious PowerShell activity',
  'Which hosts are at risk?',
  'Summarize the attack timeline',
  'What MITRE techniques are confirmed?',
];

const INITIAL_MESSAGES = [{
  role: 'assistant',
  text: 'Agentic SOC Copilot ready. I have full context on INC-2023-981. I can answer questions about entities, timelines, evidence, and recommended response actions.',
  refs: [],
}];

const CANNED_RESPONSES = {
  'How did the attacker gain access?': {
    text: 'Based on evidence collected by SENTINEL-01, the attacker likely gained initial access via **spear phishing** (T1566.001). A malicious macro in an Office attachment was executed by KR\\admin at 02:14 AM, establishing a PowerShell reverse shell.',
    refs: ['ALT-001: PowerShell execution', 'Entity: KR\\admin', 'Artifact: ps_payload.b64'],
  },
  'Show suspicious PowerShell activity': {
    text: 'SENTINEL-01 flagged 3 anomalous PowerShell executions:\n1. `svchost.exe → powershell.exe -enc [base64]` (Host-DX9, 14:02:11)\n2. `WMI spawned PS` for persistence (14:02:45)\n3. `Invoke-Mimikatz` variant via reflective injection (14:03:01)',
    refs: ['MITRE: T1059.001', 'Host: Host-DX9', 'PID: 9912'],
  },
  'Which hosts are at risk?': {
    text: 'Based on the entity graph, these hosts are at elevated risk:\n• **Host-DX9** — confirmed compromised (isolated)\n• **srv-dc01** — targeted by Silver Ticket attempt\n• **Host-WS4** — lateral movement beacon detected\n• **OT-PLC-01** — unusual Modbus activity (low confidence)',
    refs: ['Entity Graph', 'Alert: ALT-002', 'Alert: ALT-003'],
  },
  'Summarize the attack timeline': {
    text: 'Attack timeline summary for INC-2023-981:\n\n→ 02:14 Phishing email opened by KR\\admin\n→ 02:14 PowerShell reverse shell established (Host-DX9)\n→ 02:18 SENTINEL-01 detected anomaly, began investigation\n→ 14:02 Credential dump via LSASS (Mimikatz)\n→ 14:02 Host-DX9 isolated by WARDEN-07\n→ 14:03 Lateral movement to srv-dc01 (Silver Ticket)\n→ ONGOING: Blast radius assessment in progress',
    refs: ['AgentTimeline', 'INC-2023-981', 'Host: srv-dc01'],
  },
  'What MITRE techniques are confirmed?': {
    text: 'Confirmed MITRE ATT&CK TTPs in INC-2023-981:\n\nInitial Access:\n • T1566.001 — Spear Phishing Attachment\n\nExecution:\n • T1059.001 — PowerShell\n • T1047 — WMI\n\nCredential Access:\n • T1003.001 — LSASS Memory\n • T1558.003 — Kerberoasting\n\nLateral Movement:\n • T1021.002 — SMB/Windows Admin Shares\n • T1550.003 — Pass the Ticket (Silver Ticket)',
    refs: ['MITRE Navigator', 'Agent: SENTINEL-01', 'Evidence: EVD-001'],
  },
};

// ── Typing effect hook ────────────────────────────────────────────────
function useTypewriter(text, speed = 18, active = true) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!active) { setDisplayed(text); setDone(true); return; }
    setDisplayed('');
    setDone(false);
    let i = 0;
    const id = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) { clearInterval(id); setDone(true); }
    }, speed);
    return () => clearInterval(id);
  }, [text, speed, active]);

  return { displayed, done };
}

// ── Message bubble ────────────────────────────────────────────────────
function Msg({ msg, isLatestAI }) {
  const isUser = msg.role === 'user';
  const { displayed, done } = useTypewriter(msg.text, 14, isLatestAI && !isUser);

  return (
    <div className={`flex gap-2.5 animate-slide-in-up ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{
          background: isUser ? '#3B6FE322' : '#D84C7F22',
          border: `1px solid ${isUser ? '#3B6FE3' : '#D84C7F'}`,
          boxShadow: isUser ? '0 0 8px rgba(59,111,227,0.2)' : '0 0 8px rgba(216,76,127,0.2)',
        }}>
        {isUser
          ? <User size={12} style={{ color: '#3B6FE3' }} />
          : <Bot  size={12} style={{ color: '#D84C7F' }} />}
      </div>

      {/* Bubble */}
      <div className={`flex-1 max-w-[86%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1.5`}>
        <div
          className="rounded-xl px-3 py-2.5 card-elevated"
          style={{
            background: isUser ? '#3B6FE311' : '#111827',
            border: `1px solid ${isUser ? '#3B6FE322' : '#1F2937'}`,
          }}>
          <pre className={`text-xs whitespace-pre-wrap leading-relaxed ${!done && isLatestAI && !isUser ? 'typing-cursor' : ''}`}
            style={{ color: '#CBD5E1', fontFamily: 'Inter, system-ui, sans-serif' }}>
            {isLatestAI && !isUser ? displayed : msg.text}
          </pre>
        </div>

        {/* Reference chips */}
        {msg.refs?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {msg.refs.map((ref, i) => (
              <span key={i}
                className="text-xs terminal px-2 py-0.5 rounded cursor-pointer hover:brightness-125 transition-all hover-glow-magenta"
                style={{ background: '#D84C7F11', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
                ↗ {ref}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function AICopilot({ onClose }) {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [latestAIIdx, setLatestAIIdx] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = (text) => {
    const q = text || input.trim();
    if (!q || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setLoading(true);

    // Deliberate stagger: loading dots → typed response
    setTimeout(() => {
      const canned = CANNED_RESPONSES[q];
      const aiMsg = canned
        ? { role: 'assistant', text: canned.text, refs: canned.refs }
        : {
            role: 'assistant',
            text: `Analyzing INC-2023-981 context for: "${q}"\n\nCorrelating entity data, timeline events, and evidence artifacts…\n\n[Context window: 14 entities · 4 artifacts · 8 alerts · 48 tool calls]\n\nNo exact match found. Try: "How did the attacker gain access?" or "Which hosts are at risk?"`,
            refs: ['INC-2023-981'],
          };
      setMessages(prev => { const next = [...prev, aiMsg]; setLatestAIIdx(next.length - 1); return next; });
      setLoading(false);
    }, 900 + Math.random() * 400);
  };

  return (
    <div className="flex flex-col h-full" style={{ background: '#080d14' }}>

      {/* Header */}
      <div
        className="flex items-center gap-2.5 px-4 py-2.5 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0a0e17' }}>
        <div className="relative">
          <Sparkles size={13} style={{ color: '#D84C7F' }} className="animate-pulse-magenta" />
        </div>
        <span className="text-xs font-bold tracking-widest sans" style={{ color: '#E2E8F0' }}>AI COPILOT</span>
        <span className="text-xs terminal px-2 py-0.5 rounded ml-1 animate-pulse-scale"
          style={{ background: '#D84C7F18', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
          INC-2023-981
        </span>
        <div className="ml-auto flex items-center gap-2">
          <span className="flex items-center gap-1 text-xs terminal" style={{ color: '#4B5563' }}>
            <span className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: '#88C057', boxShadow: '0 0 4px #88C057' }} />
            LIVE CTX
          </span>
          {onClose && (
            <button onClick={onClose} className="p-1 rounded hover:bg-white/5 transition-colors">
              <X size={12} style={{ color: '#6B7280' }} />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {messages.map((m, i) => (
          <Msg key={i} msg={m} isLatestAI={i === latestAIIdx} />
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-2.5 animate-slide-in-up">
            <div className="w-7 h-7 rounded-full flex items-center justify-center animate-pulse-magenta"
              style={{ background: '#D84C7F22', border: '1px solid #D84C7F' }}>
              <Bot size={12} style={{ color: '#D84C7F' }} />
            </div>
            <div className="px-4 py-3 rounded-xl" style={{ background: '#111827', border: '1px solid #1F2937' }}>
              <div className="flex gap-1.5 items-center">
                {[0, 1, 2].map(i => (
                  <span key={i}
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      background: '#D84C7F',
                      animation: `pulse-dot 1s ease-in-out infinite`,
                      animationDelay: `${i * 220}ms`,
                    }} />
                ))}
                <span className="text-xs terminal ml-1" style={{ color: '#4B5563' }}>reasoning…</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips */}
      <div className="flex gap-1.5 px-3 pt-2 pb-1 overflow-x-auto border-t flex-shrink-0"
        style={{ borderColor: '#1F2937' }}>
        {SUGGESTIONS.map(s => (
          <button key={s} onClick={() => send(s)}
            className="flex-shrink-0 text-xs terminal px-2.5 py-1.5 rounded-full hover:brightness-125 transition-all action-btn"
            style={{ background: '#D84C7F0e', color: '#D84C7F99', border: '1px solid #D84C7F22' }}>
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-t flex-shrink-0" style={{ borderColor: '#1F2937' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask about entities, timelines, evidence..."
          className="flex-1 text-xs rounded-lg px-3 py-2 terminal focus:outline-none transition-all"
          style={{ background: '#111827', border: '1px solid #1F2937', color: '#9CA3AF' }}
          onFocus={e => { e.target.style.borderColor = '#D84C7F55'; e.target.style.boxShadow = '0 0 0 2px rgba(216,76,127,0.08)'; }}
          onBlur={e => { e.target.style.borderColor = '#1F2937'; e.target.style.boxShadow = 'none'; }}
        />
        <button
          onClick={() => send()}
          disabled={loading || !input.trim()}
          className="w-9 h-9 rounded-lg flex items-center justify-center transition-all action-btn"
          style={{
            background: input.trim() ? '#D84C7F22' : '#FFFFFF05',
            border: `1px solid ${input.trim() ? '#D84C7F44' : '#1F2937'}`,
          }}>
          <Send size={12} style={{ color: input.trim() ? '#D84C7F' : '#374151' }} />
        </button>
      </div>
    </div>
  );
}

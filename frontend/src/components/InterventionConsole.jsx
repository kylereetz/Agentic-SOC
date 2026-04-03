import React, { useState, useRef, useEffect } from 'react';
import { Terminal, ChevronRight, Check, X, Edit3, Lightbulb } from 'lucide-react';

const HISTORY = [
  { type: 'system', text: 'Intervention Console initialized. Connected to SENTINEL-01.' },
  { type: 'system', text: 'Pending action: WARDEN-07 requests approval to run isolate_host --id "Host-DX9"' },
  { type: 'agent', text: '[WARDEN-07] Isolation command ready. Awaiting analyst authorization.' },
  { type: 'user', text: 'approve' },
  { type: 'output', text: '✓ Action approved. Host-DX9 isolation initiated. Firewall ruleset updated.' },
  { type: 'agent', text: '[HERALD-03] Lateral movement scan on 192.168.1.0/24 ready. Depth=2. Approve?' },
];

const QUICK_CMDS = [
  { label: 'approve', color: '#88C057' },
  { label: 'reject', color: '#EF4444' },
  { label: 'hint "focus on DC-01"', color: '#D84C7F' },
  { label: 'setparam --depth 3', color: '#3B6FE3' },
  { label: 'status', color: '#E5A862' },
];

const LINE_COLORS = {
  system: '#4B5563',
  agent:  '#3B6FE3',
  user:   '#88C057',
  output: '#CBD5E1',
  error:  '#EF4444',
};

export default function InterventionConsole() {
  const [history, setHistory] = useState(HISTORY);
  const [input, setInput] = useState('');
  const [cmdHistory, setCmdHistory] = useState([]);
  const [historyIdx, setHistoryIdx] = useState(-1);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const executeCommand = (cmd) => {
    const trimmed = cmd.trim();
    if (!trimmed) return;
    const newHistory = [...history, { type: 'user', text: trimmed }];
    setCmdHistory(prev => [trimmed, ...prev]);

    let response;
    if (trimmed === 'approve') {
      response = { type: 'output', text: '✓ Action approved and dispatched to containment mesh.' };
    } else if (trimmed === 'reject') {
      response = { type: 'output', text: '✕ Action rejected. Agent notified to seek alternative.' };
    } else if (trimmed === 'status') {
      response = { type: 'output', text: 'SENTINEL-01: ACTIVE (48 tools)\nHERALD-03: ACTIVE (18 tools)\nWARDEN-07: WAITING APPROVAL\nRECON-02: ACTIVE (33 tools)' };
    } else if (trimmed.startsWith('hint')) {
      response = { type: 'output', text: `✓ Hint injected into SENTINEL-01 context: ${trimmed.replace('hint', '').trim()}` };
    } else {
      response = { type: 'output', text: `Unknown command: ${trimmed}. Type 'help' for commands.` };
    }

    setHistory([...newHistory, response]);
    setInput('');
    setHistoryIdx(-1);
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter') { executeCommand(input); }
    else if (e.key === 'ArrowUp') {
      const idx = Math.min(historyIdx + 1, cmdHistory.length - 1);
      setHistoryIdx(idx);
      setInput(cmdHistory[idx] || '');
    } else if (e.key === 'ArrowDown') {
      const idx = Math.max(historyIdx - 1, -1);
      setHistoryIdx(idx);
      setInput(idx === -1 ? '' : cmdHistory[idx]);
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <Terminal size={13} style={{ color: '#88C057' }} />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>INTERVENTION CONSOLE</span>
        <span className="ml-auto flex items-center gap-1.5 text-xs terminal" style={{ color: '#88C057' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-blink" />
          CONNECTED: SENTINEL-01
        </span>
      </div>

      {/* Terminal Output */}
      <div className="flex-1 overflow-y-auto p-3 terminal text-xs space-y-1">
        {history.map((line, i) => (
          <div key={i} className="flex items-start gap-2">
            {line.type === 'user'
              ? <span style={{ color: '#4B5563' }} className="flex-shrink-0">analyst@soc:~$</span>
              : <span style={{ color: '#1F2937' }} className="flex-shrink-0">{'>'}</span>
            }
            <pre className="whitespace-pre-wrap break-words" style={{ color: LINE_COLORS[line.type] || '#CBD5E1' }}>
              {line.text}
            </pre>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Quick Buttons */}
      <div className="flex items-center gap-2 px-3 py-2 border-t flex-shrink-0 overflow-x-auto"
        style={{ borderColor: '#1F2937' }}>
        <span className="text-xs terminal flex-shrink-0" style={{ color: '#4B5563' }}>Quick:</span>
        {QUICK_CMDS.map(({ label, color }) => (
          <button key={label} onClick={() => executeCommand(label)}
            className="flex-shrink-0 text-xs terminal px-2 py-1 rounded hover:brightness-125 transition-all"
            style={{ background: `${color}12`, color, border: `1px solid ${color}33` }}>
            {label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 px-3 py-2 border-t flex-shrink-0"
        style={{ borderColor: '#1F2937' }}>
        <span className="terminal text-xs flex-shrink-0" style={{ color: '#4B5563' }}>analyst@soc:~$</span>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type a command (approve, reject, hint '...', setparam...)"
          className="flex-1 terminal text-xs bg-transparent focus:outline-none"
          style={{ color: '#88C057', caretColor: '#88C057' }}
          autoFocus
        />
        <button onClick={() => executeCommand(input)}
          className="p-1.5 rounded hover:bg-white/5 transition-colors">
          <ChevronRight size={13} style={{ color: '#4B5563' }} />
        </button>
      </div>
    </div>
  );
}

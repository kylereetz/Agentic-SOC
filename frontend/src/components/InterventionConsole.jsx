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

  // Game Theory State (derived from SENTINEL-RESPONDER)
  const [payoffMatrix] = useState([
    [5.0,  8.0,  5.0], // Quarantine
    [-2.0, 5.0, 10.0], // Honeypot
    [2.0, -8.0, -2.0], // RateLimit
    [-5.0,-10.0, 5.0]  // Monitor
  ]);
  const [msne] = useState([0.45, 0.25, 0.15, 0.15]); // Mixed Strategy probabilities

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
    <div className="flex flex-col h-full overflow-hidden" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <Terminal size={13} style={{ color: '#88C057' }} />
        <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>INTERVENTION CONSOLE</span>
        <span className="ml-auto flex items-center gap-1.5 text-xs terminal" style={{ color: '#88C057' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-blink" />
          CONNECTED: SENTINEL-RESPONDER
        </span>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Terminal Section */}
        <div className="flex flex-col flex-1 min-w-0">
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
              placeholder="Type a command..."
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

        {/* Defense Matrix Panel (Game Theory HUD) */}
        <div className="w-64 border-l overflow-y-auto p-4 flex flex-col gap-4" 
          style={{ borderColor: '#1F2937', background: '#0d1117' }}>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb size={12} style={{ color: '#E5A862' }} />
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>DEFENSE MATRIX</span>
            </div>
            <p className="text-[10px] terminal opacity-50 mb-3">MSNE Mixed Strategy Probabilities (Fictitious Play Solver)</p>
            
            <div className="space-y-3">
              {['QUARANTINE', 'HONEYPOT', 'RATELIMIT', 'MONITOR'].map((strat, i) => (
                <div key={strat} className="space-y-1">
                  <div className="flex justify-between text-[9px] terminal">
                    <span style={{ color: i === 0 ? '#88C057' : '#9CA3AF' }}>{strat}</span>
                    <span style={{ color: '#E2E8F0' }}>{(msne[i]*100).toFixed(0)}%</span>
                  </div>
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: '#1F2937' }}>
                    <div className="h-full rounded-full transition-all duration-1000" 
                      style={{ width: `${msne[i] * 100}%`, background: i === 0 ? '#88C057' : '#3B6FE366' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t pt-4" style={{ borderColor: '#1F2937' }}>
            <span className="text-xs terminal block mb-2 opacity-50">PAYOFF MATRIX (ZERO-SUM)</span>
            <div className="grid grid-cols-3 gap-1">
              {payoffMatrix.map((row, r) => (
                row.map((val, c) => (
                  <div key={`${r}-${c}`} 
                    className="aspect-square flex items-center justify-center text-[9px] terminal rounded-sm"
                    style={{ 
                      background: val > 0 ? '#88C05710' : val < 0 ? '#EF444410' : '#111827',
                      color: val > 0 ? '#88C057' : val < 0 ? '#EF4444' : '#4B5563',
                      border: '1px solid #1F2937'
                    }}>
                    {val > 0 ? '+' : ''}{val}
                  </div>
                ))
              ))}
            </div>
            <div className="flex justify-between mt-1 text-[8px] terminal opacity-30 text-center">
              <span>EVAS</span>
              <span>ESCA</span>
              <span>PERS</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

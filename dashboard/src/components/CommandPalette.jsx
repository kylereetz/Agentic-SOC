import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Command, Search, Zap, Server, User, Shield, Key, Eye, ArrowRight } from 'lucide-react';
import { useSOC, ENTITY_DB } from '../store/SOCContext';

const COMMANDS = [
  { id: 'open-inv',    label: 'Open Investigation INC-2023-981',  icon: Eye,    group: 'Investigations', action: 'nav:Investigations' },
  { id: 'open-alerts', label: 'Open Alert Queue',                  icon: Zap,    group: 'Navigation',     action: 'nav:Alert Queue' },
  { id: 'open-agents', label: 'View Agent Fleet',                  icon: Shield, group: 'Navigation',     action: 'nav:Agents' },
  { id: 'open-analytics',label: 'Analytics Dashboard',             icon: Eye,    group: 'Navigation',     action: 'nav:Analytics' },
  { id: 'open-sim',    label: 'Simulation Mode',                   icon: Zap,    group: 'Navigation',     action: 'nav:Simulation Mode' },
  { id: 'find-host-dx9',label: 'Find Host → Host-DX9',            icon: Server, group: 'Entities',       action: 'entity:Host-DX9' },
  { id: 'find-srv-dc', label: 'Find Host → srv-dc01',             icon: Server, group: 'Entities',       action: 'entity:srv-dc01' },
  { id: 'find-ip',     label: 'Find IP → 192.168.1.105',          icon: Server, group: 'Entities',       action: 'entity:192.168.1.105' },
  { id: 'find-user',   label: 'Find User → KR\\admin',            icon: User,   group: 'Entities',       action: 'entity:KR\\admin' },
  { id: 'isolate',     label: 'Isolate Device — Host-DX9',        icon: Shield, group: 'Actions',        action: 'approval:ACT-001' },
  { id: 'disable-acct',label: 'Disable Account — KR\\admin',      icon: User,   group: 'Actions',        action: 'approval:ACT-002' },
  { id: 'approve-all', label: 'Approve All Pending Actions',       icon: Zap,    group: 'Actions',        action: 'approve-all' },
  { id: 'reset-pw',    label: 'Reset Password — KR\\admin',       icon: Key,    group: 'Actions',        action: 'reset-pwd' },
  { id: 'copilot',     label: 'Open AI Copilot',                   icon: Zap,    group: 'Tools',          action: 'copilot:open' },
];

function fuzzyMatch(str, query) {
  if (!query) return true;
  const s = str.toLowerCase();
  const q = query.toLowerCase();
  let qi = 0;
  for (let i = 0; i < s.length && qi < q.length; i++) {
    if (s[i] === q[qi]) qi++;
  }
  return qi === q.length;
}

const GROUP_ORDER = ['Navigation', 'Investigations', 'Entities', 'Actions', 'Tools'];

export default function CommandPalette({ onNavigate, onOpenCopilot }) {
  const { cmdPaletteOpen, setCmdPaletteOpen, clickEntity, setApprovalAction, pendingActions } = useSOC();
  const [query, setQuery] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (cmdPaletteOpen) {
      setQuery('');
      setSelectedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [cmdPaletteOpen]);

  const filtered = COMMANDS.filter(c => fuzzyMatch(c.label, query));

  const grouped = GROUP_ORDER.reduce((acc, g) => {
    const items = filtered.filter(c => c.group === g);
    if (items.length) acc.push({ group: g, items });
    return acc;
  }, []);

  const flat = grouped.flatMap(g => g.items);

  const execute = useCallback((cmd) => {
    setCmdPaletteOpen(false);
    const [type, payload] = cmd.action.split(':');
    if (type === 'nav')      onNavigate?.(payload);
    if (type === 'entity')   clickEntity(payload);
    if (type === 'approval') {
      const action = pendingActions.find(a => a.id === payload);
      if (action) setApprovalAction(action);
    }
    if (type === 'copilot')  onOpenCopilot?.();
  }, [clickEntity, setCmdPaletteOpen, onNavigate, onOpenCopilot, pendingActions, setApprovalAction]);

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIdx(i => Math.min(i + 1, flat.length - 1)); }
    if (e.key === 'ArrowUp')   { e.preventDefault(); setSelectedIdx(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && flat[selectedIdx]) execute(flat[selectedIdx]);
    if (e.key === 'Escape') setCmdPaletteOpen(false);
  };

  useEffect(() => { setSelectedIdx(0); }, [query]);

  if (!cmdPaletteOpen) return null;

  let runningIdx = 0;

  return (
    <div className="fixed inset-0 z-[200] flex items-start justify-center pt-24"
      style={{ background: 'rgba(11,17,23,0.85)', backdropFilter: 'blur(6px)' }}
      onClick={() => setCmdPaletteOpen(false)}>
      <div className="w-full max-w-lg rounded-xl overflow-hidden shadow-2xl animate-slide-in"
        style={{ background: '#111827', border: '1px solid #3B6FE355', boxShadow: '0 0 40px rgba(59,111,227,0.2)' }}
        onClick={e => e.stopPropagation()}>

        {/* Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b" style={{ borderColor: '#1F2937' }}>
          <Command size={14} style={{ color: '#3B6FE3' }} />
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search commands, entities, actions..."
            className="flex-1 text-sm bg-transparent focus:outline-none terminal"
            style={{ color: '#E2E8F0', caretColor: '#3B6FE3' }}
          />
          <kbd className="text-xs terminal px-1.5 py-0.5 rounded" style={{ background: '#FFFFFF08', color: '#4B5563' }}>ESC</kbd>
        </div>

        {/* Results */}
        <div className="overflow-y-auto max-h-[360px] py-2">
          {grouped.length === 0 && (
            <p className="text-xs terminal text-center py-6" style={{ color: '#4B5563' }}>No commands found</p>
          )}
          {grouped.map(({ group, items }) => (
            <div key={group}>
              <p className="text-xs terminal px-4 py-1.5 uppercase tracking-widest" style={{ color: '#4B5563' }}>{group}</p>
              {items.map(cmd => {
                const idx = runningIdx++;
                const isSelected = idx === selectedIdx;
                const Icon = cmd.icon;
                return (
                  <button key={cmd.id}
                    onMouseEnter={() => setSelectedIdx(idx)}
                    onClick={() => execute(cmd)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-all"
                    style={{ background: isSelected ? '#3B6FE318' : 'transparent', color: isSelected ? '#E2E8F0' : '#9CA3AF' }}>
                    <Icon size={13} style={{ color: isSelected ? '#3B6FE3' : '#4B5563', flexShrink: 0 }} />
                    <span className="flex-1">{cmd.label}</span>
                    {isSelected && <ArrowRight size={12} style={{ color: '#3B6FE3' }} />}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-4 px-4 py-2 border-t text-xs terminal" style={{ borderColor: '#1F2937', color: '#4B5563' }}>
          <span><kbd className="terminal px-1 rounded" style={{ background: '#FFFFFF08' }}>↑↓</kbd> Navigate</span>
          <span><kbd className="terminal px-1 rounded" style={{ background: '#FFFFFF08' }}>↵</kbd> Execute</span>
          <span><kbd className="terminal px-1 rounded" style={{ background: '#FFFFFF08' }}>⌘K</kbd> Toggle</span>
        </div>
      </div>
    </div>
  );
}

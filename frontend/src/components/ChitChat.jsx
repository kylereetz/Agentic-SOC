import React, { useState, useRef, useEffect } from 'react';
import { Send, X, Bot, User, Sparkles } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

const SUGGESTIONS = [
  'How did the attacker gain access?',
  'Show suspicious PowerShell activity',
  'Which hosts are at risk?',
  'Summarize the attack timeline',
  'What MITRE techniques are confirmed?',
];

const getWelcomeMessage = (caseId) => ({
  role: 'assistant',
  text: `ChitChat ready. I have full context on ${caseId}. I can answer questions about entities, timelines, evidence, and recommended response actions.`,
  refs: [],
});

// Responses are fetched from the internal model API in real-time.

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
        }}
      >
        {isUser
          ? <User size={12} style={{ color: '#3B6FE3' }} />
          : <Bot size={12} style={{ color: '#D84C7F' }} />}
      </div>

      {/* Bubble */}
      <div className={`flex-1 max-w-[86%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1.5`}>
        <div
          className="rounded-xl px-3 py-2.5 card-elevated"
          style={{
            background: isUser ? '#3B6FE311' : '#111827',
            border: `1px solid ${isUser ? '#3B6FE322' : '#1F2937'}`,
          }}
        >
          <pre className={`text-xs whitespace-pre-wrap leading-relaxed ${!done && isLatestAI && !isUser ? 'typing-cursor' : ''}`}
            style={{ color: '#CBD5E1' }}>
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

export default function ChitChat({ onClose }) {
  const { authenticatedFetch } = useAuth();
  const { investigations } = useSOC();
  
  const activeCaseId = investigations && investigations.length > 0 
    ? investigations[0].id 
    : 'Global SOC';

  const [messages, setMessages] = useState(() => {
    const saved = localStorage.getItem('chitchat_history');
    return saved ? JSON.parse(saved) : [getWelcomeMessage(activeCaseId)];
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [latestAIIdx, setLatestAIIdx] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('chitchat_history', JSON.stringify(messages));
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text) => {
    const q = text || input.trim();
    if (!q || loading) return;
    
    setInput('');
    const userMsg = { role: 'user', text: q };
    const currentMessages = [...messages, userMsg];
    setMessages(currentMessages);
    setLoading(true);

    try {
      console.log(`[ChitChat] Sending query: ${q}`);
      // Note: Backend expects { query: str, history: List[Dict[role, text]] }
      // We skip the initial welcome message from the history if it's role: 'assistant'
      const history = currentMessages.slice(1, -1); 

      const response = await authenticatedFetch('http://localhost:8000/api/v1/chitchat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, history })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Internal Model API returned error');
      }

      const data = await response.json();
      const aiMsg = { 
        role: 'assistant', 
        text: data.response || 'No response from model.', 
        refs: ['FLYWAY-COMMUNICATOR', 'Local-Ollama']
      };
      
      setMessages(prev => {
        const next = [...prev, aiMsg];
        setLatestAIIdx(next.length - 1);
        return next;
      });
    } catch (err) {
      console.error('ChitChat Error:', err);
      const errMsg = { 
        role: 'assistant', 
        text: `⚠️ Error: ${err.message}. Ensure Ollama is running (llama3-soc) and the backend is online.`,
        refs: ['OLLAMA_TIMEOUT', 'CONNECTION_ERROR']
      };
      setMessages(prev => {
        const next = [...prev, errMsg];
        setLatestAIIdx(next.length - 1); // Ensure typewriter/scrolling works for error
        return next;
      });
    } finally {
      setLoading(false);
    }
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
        <span className="text-xs font-bold tracking-widest sans" style={{ color: '#E2E8F0' }}>CHITCHAT</span>
        <span className="text-xs terminal px-2 py-0.5 rounded ml-1 animate-pulse-scale"
          style={{ background: '#D84C7F18', color: '#D84C7F', border: '1px solid #D84C7F33' }}>
          {activeCaseId}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <span className="flex items-center gap-1 text-xs terminal" style={{ color: '#4B5563' }}>
            <span className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: '#88C057', boxShadow: '0 0 4px #88C057' }} />
            LIVE CTX
          </span>
          <button 
            onClick={() => { if(confirm('Clear history?')) { setMessages([getWelcomeMessage(activeCaseId)]); localStorage.removeItem('chitchat_history'); } }}
            className="text-[10px] terminal px-1.5 py-0.5 rounded hover:bg-white/10 transition-colors"
            style={{ color: '#4B5563', border: '1px solid #1F2937' }}>
            CLEAR
          </button>
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

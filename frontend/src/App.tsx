import React, { useState } from 'react';
import { Send, Bot, Code2, Rss, Calendar } from 'lucide-react';
import './index.css';

export default function App() {
  const [messages, setMessages] = useState<{role: 'user'|'agent', content: string}[]>([
    {role: 'agent', content: 'Hello! I am your Agent Orchestrator. How can the team help you today?'}
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, {role: 'user', content: userMsg}]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/chat?message=${encodeURIComponent(userMsg)}`, {
        method: 'POST'
      });
      const data = await res.json();
      setMessages(prev => [...prev, {role: 'agent', content: data.response}]);
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, {role: 'agent', content: 'Sorry, the backend is currently unreachable.'}]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Sidebar */}
      <div style={{ 
        width: '260px', 
        background: 'var(--panel-bg)',
        borderRight: '1px solid var(--border-color)',
        backdropFilter: 'blur(10px)',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Bot size={28} color="var(--accent-color)" />
          <h1 style={{ fontSize: '1.2rem', fontWeight: 600, letterSpacing: '0.5px' }}>Agent Team</h1>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Specialists</p>
          <AgentTab icon={<Code2 size={18}/>} label="Coding Agent" />
          <AgentTab icon={<Rss size={18}/>} label="Research Agent" />
          <AgentTab icon={<Calendar size={18}/>} label="Comms Agent" />
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        
        {/* Header */}
        <header style={{ 
          height: '70px', 
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 2rem',
          background: 'rgba(11, 15, 25, 0.8)',
          backdropFilter: 'blur(8px)'
        }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 500 }}>Central Orchestrator</h2>
        </header>

        {/* Chat Log */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {messages.map((m, i) => (
            <div key={i} style={{ 
              display: 'flex', 
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' 
            }}>
              <div style={{
                maxWidth: '70%',
                padding: '1rem 1.25rem',
                borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                background: m.role === 'user' ? 'var(--accent-color)' : 'var(--panel-bg)',
                border: m.role === 'agent' ? '1px solid var(--border-color)' : 'none',
                boxShadow: m.role === 'user' ? '0 4px 15px var(--accent-glow)' : 'none',
                lineHeight: 1.5,
                fontSize: '0.95rem'
              }}>
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
             <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
               <div style={{ padding: '1rem', background: 'var(--panel-bg)', borderRadius: '18px 18px 18px 4px', border: '1px solid var(--border-color)'}}>
                 <Bot size={20} style={{ animation: 'spin 2s linear infinite' }} />
               </div>
             </div>
          )}
        </div>

        {/* Input Area */}
        <div style={{ padding: '1.5rem 2rem' }}>
          <div style={{ 
            display: 'flex', 
            background: 'var(--panel-bg)', 
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '0.5rem 1rem',
            alignItems: 'center',
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)'
          }}>
            <input 
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Assign a task to the team..."
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                color: 'white',
                outline: 'none',
                fontSize: '1rem',
                padding: '0.5rem'
              }}
            />
            <button 
              onClick={handleSend}
              style={{
                background: 'var(--accent-color)',
                border: 'none',
                borderRadius: '8px',
                width: '40px',
                height: '40px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                cursor: 'pointer',
                transition: 'transform 0.2s'
              }}
              onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'}
              onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentTab({ icon, label }: { icon: React.ReactNode, label: string }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      padding: '0.75rem 1rem',
      borderRadius: '8px',
      cursor: 'pointer',
      color: 'var(--text-muted)',
      transition: 'all 0.2s',
      border: '1px solid transparent'
    }}
    onMouseOver={e => {
        e.currentTarget.style.color = 'var(--text-main)';
        e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)';
    }}
    onMouseOut={e => {
        e.currentTarget.style.color = 'var(--text-muted)';
        e.currentTarget.style.background = 'transparent';
        e.currentTarget.style.borderColor = 'transparent';
    }}
    >
      {icon}
      <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{label}</span>
      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', marginLeft: 'auto', boxShadow: '0 0 5px #10b981'}} />
    </div>
  );
}

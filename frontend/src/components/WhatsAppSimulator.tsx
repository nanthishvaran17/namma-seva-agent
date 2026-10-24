import React, { useState } from 'react';
import { Send, Smartphone, ShieldCheck, CheckCheck } from 'lucide-react';
import { ApiClient } from '../services/api';
import { FormattedText } from './FormattedText';

export const WhatsAppSimulator: React.FC = () => {
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'agent'; text: string; time: string }>>([
    {
      sender: 'agent',
      text: 'Vanakkam! Namma Seva WhatsApp Bot-ku varaverkirom. Enna service vendum? (e.g. "Community certificate", "Income certificate", "Scholarship")',
      time: '10:00 AM'
    }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputVal.trim();
    if (!text || loading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [...prev, { sender: 'user', text, time: timeStr }]);
    setInputVal('');
    setLoading(true);

    try {
      const res = await ApiClient.simulateWhatsApp('919876543210', text);
      setMessages((prev) => [
        ...prev,
        { sender: 'agent', text: res.reply_text, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { sender: 'agent', text: 'Error simulating WhatsApp delivery.', time: timeStr }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ textAlign: 'center', padding: '1rem 0' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 className="section-title" style={{ fontSize: '1.75rem', marginBottom: '0.4rem' }}>
          WhatsApp Cloud API Local Simulator
        </h2>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: '#fef3c7', color: '#92400e', padding: '0.3rem 0.85rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 700 }}>
          <span>Notice: Clearly labeled local developer simulator — not connected to live Meta billing</span>
        </div>
      </div>

      <div className="phone-frame">
        {/* Header */}
        <div className="phone-header">
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#00a884', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 800, fontSize: '0.85rem' }}>
            NS
          </div>
          <div>
            <div style={{ fontSize: '0.88rem', fontWeight: 700 }}>Namma Seva Bot (Official)</div>
            <div style={{ fontSize: '0.7rem', color: '#8696a0' }}>Online • WhatsApp Cloud API</div>
          </div>
        </div>

        {/* Screen Messages */}
        <div className="phone-screen">
          {messages.map((m, idx) => (
            <div key={idx} className={`wa-bubble ${m.sender === 'user' ? 'outgoing' : 'incoming'}`}>
              <FormattedText content={m.text} />
              <div style={{ fontSize: '0.65rem', color: '#8696a0', textAlign: 'right', marginTop: '3px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '3px' }}>
                <span>{m.time}</span>
                {m.sender === 'user' && <CheckCheck size={12} color="#53bdeb" />}
              </div>
            </div>
          ))}

          {loading && (
            <div className="wa-bubble incoming" style={{ fontStyle: 'italic', color: '#8696a0' }}>
              typing...
            </div>
          )}
        </div>

        {/* Phone Input Bar */}
        <form className="phone-input-bar" onSubmit={handleSend}>
          <input
            type="text"
            className="phone-input"
            placeholder="Type a message (Tamil/Tanglish)..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
          />
          <button
            type="submit"
            style={{ background: '#00a884', color: 'white', border: 'none', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
};

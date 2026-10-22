import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ExternalLink, ShieldCheck, AlertTriangle, ArrowRight, CheckCircle2, Clock } from 'lucide-react';
import { ApiClient } from '../services/api';
import type { ChatMessage } from '../types';

interface AssistantChatProps {
  language: string;
  initialQuery?: string;
  onStartServiceTask?: (serviceId: string) => void;
}

export const AssistantChat: React.FC<AssistantChatProps> = ({
  language,
  initialQuery,
  onStartServiceTask,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'AGENT',
      content:
        language === 'ta'
          ? 'வணக்கம்! நான் உங்கள் நம்ம சேவை AI வழிகாட்டி. சாதிச் சான்றிதழ், வருமானச் சான்றிதழ், முதல் தலைமுறை பட்டதாரி சலுகை அல்லது கல்வி உதவித்தொகை பற்றி நீங்கள் எதையும் கேட்கலாம். உங்களுக்கு என்ன உதவி வேண்டும்?'
          : 'Vanakkam! I am your Namma Seva AI Guide. Ask me anything about Tamil Nadu certificates (Community, Income, Nativity, First Graduate) or student scholarships.',
      citations: [
        { title: 'TNeGA e-Sevai Portal', url: 'https://www.tnesevai.tn.gov.in/' }
      ]
    }
  ]);

  const [inputVal, setInputVal] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    if (initialQuery) {
      handleSendMessage(initialQuery);
    }
  }, [initialQuery]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputVal.trim();
    if (!text || loading) return;

    // Add user message
    const userMsg: ChatMessage = {
      sender: 'USER',
      content: text,
      language
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputVal('');
    setLoading(true);

    try {
      const res = await ApiClient.sendChatMessage(text, undefined, language);
      const agentMsg: ChatMessage = {
        sender: 'AGENT',
        content: res.message,
        language: res.language,
        citations: res.citations,
        action_cards: res.action_cards
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        sender: 'AGENT',
        content:
          language === 'ta'
            ? 'மன்னிக்கவும், தகவல்களைப் பெறுவதில் சிறு பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.'
            : 'Sorry, there was a temporary issue processing your request. Please try again.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const sampleSuggestions = [
    'Enakku community certificate venum',
    'வருமானச் சான்றிதழ் செல்லுபடியாகும் காலம் என்ன?',
    'First graduate certificate eligibility rules',
    'Post matric scholarship-ku enna documents venum?'
  ];

  return (
    <div className="chat-window">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-title">
          <Bot size={20} color="#0f3460" />
          <span>
            {language === 'ta'
              ? 'நம்ம சேவை AI வழிகாட்டி — Tamil Nadu Civic Guide'
              : 'Namma Seva Agent AI — Official Guide'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="verified-tag">
            <ShieldCheck size={13} />
            <span>Official Rules Grounded</span>
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-body">
        {messages.map((m, idx) => (
          <div key={idx} className={`msg-row ${m.sender === 'USER' ? 'user' : 'agent'}`}>
            <div className={`avatar-icon ${m.sender === 'USER' ? 'user' : 'agent'}`}>
              {m.sender === 'USER' ? <User size={18} /> : <Bot size={18} />}
            </div>

            <div style={{ maxWidth: '100%' }}>
              <div className={`msg-bubble ${m.sender === 'USER' ? 'user' : 'agent'}`}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>

                {/* Structured Action Cards */}
                {m.action_cards && m.action_cards.length > 0 && (
                  <div style={{ marginTop: '0.85rem' }}>
                    {m.action_cards.map((card: any, cIdx: number) => {
                      if (card.card_type === 'DEPENDENCY_PLAN' || card.plan) {
                        const plan = card.plan;
                        return (
                          <div key={cIdx} className="plan-step-card">
                            <div className="plan-step-header">
                              <span className="plan-step-badge">
                                Action Plan: {plan.pending_services_count} steps
                              </span>
                              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                                Est. Fee: ₹{plan.total_estimated_fee_inr}
                              </span>
                            </div>

                            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.4rem' }}>
                              Sequential Prerequisites:
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                              {plan.plan_steps?.map((step: any, sIdx: number) => (
                                <div
                                  key={sIdx}
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    padding: '0.45rem 0.65rem',
                                    background: '#f8fafc',
                                    borderRadius: '6px',
                                    border: '1px solid #e2e8f0',
                                    fontSize: '0.82rem'
                                  }}
                                >
                                  <div>
                                    <span style={{ fontWeight: 700, marginRight: '6px' }}>{step.step_order}.</span>
                                    <span>{step.service_name_en}</span>
                                    <span style={{ color: 'var(--text-muted)', marginLeft: '6px' }}>({step.service_name_ta})</span>
                                  </div>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span style={{ color: '#059669', fontWeight: 600 }}>₹{step.fee_inr}</span>
                                    {onStartServiceTask && (
                                      <button
                                        type="button"
                                        style={{ background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '4px', padding: '0.2rem 0.5rem', fontSize: '0.72rem', cursor: 'pointer' }}
                                        onClick={() => onStartServiceTask(step.service_id)}
                                      >
                                        Start
                                      </button>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      }

                      if (card.card_type === 'SERVICE_PLAN') {
                        return (
                          <div key={cIdx} className="plan-step-card" style={{ borderLeft: '4px solid var(--primary)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <div>
                                <h4 style={{ fontSize: '0.92rem', fontWeight: 700 }}>{card.name_en}</h4>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{card.name_ta}</div>
                              </div>
                              {onStartServiceTask && (
                                <button
                                  type="button"
                                  className="btn-primary"
                                  style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
                                  onClick={() => onStartServiceTask(card.service_id)}
                                >
                                  <span>{language === 'ta' ? 'பணியைத் தொடங்குக' : 'Start Task'}</span>
                                  <ArrowRight size={13} />
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      }

                      return null;
                    })}
                  </div>
                )}

                {/* Citations */}
                {m.citations && m.citations.length > 0 && (
                  <div className="citation-list">
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                      <ShieldCheck size={12} color="#059669" /> Sources:
                    </span>
                    {m.citations.map((c, cIdx) => (
                      <a
                        key={cIdx}
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="citation-tag"
                      >
                        <span>{c.title}</span>
                        <ExternalLink size={11} />
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="msg-row agent">
            <div className="avatar-icon agent">
              <Bot size={18} />
            </div>
            <div className="msg-bubble agent" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={16} className="animate-spin" />
              <span>{language === 'ta' ? 'அரசு விதிகளை சரிபார்க்கிறது...' : 'Verifying official rules & citations...'}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested chips if conversation is short */}
      {messages.length <= 2 && (
        <div style={{ padding: '0.5rem 1.5rem', background: '#f8fafc', display: 'flex', gap: '0.5rem', overflowX: 'auto', borderTop: '1px solid var(--border-color)' }}>
          {sampleSuggestions.map((s, idx) => (
            <button
              key={idx}
              type="button"
              style={{ background: 'white', border: '1px solid var(--border-color)', borderRadius: '9999px', padding: '0.25rem 0.75rem', fontSize: '0.78rem', color: 'var(--primary)', cursor: 'pointer', whiteSpace: 'nowrap' }}
              onClick={() => handleSendMessage(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input Composer */}
      <form
        className="chat-input-area"
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
      >
        <input
          type="text"
          className="chat-input"
          placeholder={
            language === 'ta'
              ? 'உங்கள் கேள்வியை தமிழ் அல்லது ஆங்கிலத்தில் தட்டச்சு செய்யவும்...'
              : 'Ask a question in Tamil, Tanglish, or English...'
          }
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
        />
        <button type="submit" className="chat-send-btn" disabled={loading}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};

import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, CheckCheck, Mic, Paperclip, Phone, MoreVertical, Sparkles, Shield, ArrowUpRight } from 'lucide-react';
import { ApiClient } from '../services/api';

interface FloatingWhatsAppProps {
  language: string;
}

export const FloatingWhatsApp: React.FC<FloatingWhatsAppProps> = ({ language }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Array<{ sender: 'user' | 'bot'; text: string; time: string }>>([
    {
      sender: 'bot',
      text:
        language === 'ta'
          ? 'வணக்கம்! நான் தமிழ்நாடு நம்ம சேவை WhatsApp AI வழிகாட்டி.\nசாதி, வருமானம், முதல் பட்டதாரி சான்றிதழ்கள் அல்லது ஸ்காலர்ஷிப் பற்றி நீங்கள் எதையும் கேட்கலாம்.'
          : 'Vanakkam! I am your Namma Seva WhatsApp AI Guide.\nAsk me anything about Community, Income, First Graduate certificates, or scholarships.',
      time: '10:00 AM'
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(1);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0);
      chatScrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [isOpen, messages]);

  const handleSend = async (customText?: string) => {
    const text = customText || inputText.trim();
    if (!text || loading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages((prev) => [...prev, { sender: 'user', text, time: timeStr }]);
    setInputText('');
    setLoading(true);

    try {
      const res = await ApiClient.simulateWhatsApp('919876543210', text);
      const replyTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: res.reply_text, time: replyTime }
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: language === 'ta' ? 'மன்னிக்கவும், தகவல்களைப் பெறுவதில் சிறு தாமதம். மீண்டும் அனுப்பவும்.' : 'Temporary delay. Please try again.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPills = [
    { label: language === 'ta' ? 'சாதி சான்றிதழ்' : 'Community Cert', query: 'சாதிச் சான்றிதழ் பெற என்ன ஆவணங்கள் தேவை?' },
    { label: language === 'ta' ? 'வருமான சான்று' : 'Income Cert', query: 'வருமானச் சான்றிதழ் பெற எப்படி விண்ணப்பிப்பது?' },
    { label: language === 'ta' ? 'முதல் பட்டதாரி' : 'First Graduate', query: 'First graduate certificate eligibility in Tamil Nadu' },
    { label: language === 'ta' ? 'ரேஷன் அட்டை' : 'Smart Ration Card', query: 'புதிய ஸ்மார்ட் குடும்ப அட்டை விண்ணப்பிக்க முறை' }
  ];

  return (
    <div className="floating-whatsapp-container">
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          className="floating-wa-btn"
          onClick={() => setIsOpen(true)}
          title="Open WhatsApp AI Assistant"
        >
          <div className="wa-icon-glow">
            <MessageCircle size={28} color="white" />
          </div>
          <span className="wa-btn-label">
            {language === 'ta' ? 'WhatsApp உதவி' : 'Chat on WhatsApp'}
          </span>
          {unreadCount > 0 && (
            <span className="wa-unread-badge">{unreadCount}</span>
          )}
        </button>
      )}

      {/* Floating WhatsApp Chat Window */}
      {isOpen && (
        <div className="floating-wa-card">
          {/* Header */}
          <div className="wa-top-bar">
            <div className="wa-profile-row">
              <div className="wa-avatar-badge">
                <span>TN</span>
              </div>
              <div className="wa-profile-info">
                <div className="wa-profile-name">
                  <span>நம்ம சேவை Bot (Official)</span>
                  <Shield size={13} className="text-emerald-300" />
                </div>
                <div className="wa-status-text">
                  <span className="online-dot" /> Online • Cloud AI Assistant
                </div>
              </div>
            </div>

            <div className="wa-header-actions">
              <a
                href="https://wa.me/919876543210?text=Vanakkam%20Namma%20Seva%20AI"
                target="_blank"
                rel="noreferrer"
                className="wa-header-icon-btn"
                title="Open in WhatsApp Web / App"
              >
                <ArrowUpRight size={17} />
              </a>
              <button
                className="wa-header-icon-btn"
                onClick={() => setIsOpen(false)}
                title="Close chat"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Quick Info Ribbon */}
          <div className="wa-info-ribbon">
            <Sparkles size={13} />
            <span>{language === 'ta' ? '100% இலவச உடனடி வழிகாட்டி — 24x7 கிடைக்கும்' : 'Instant 24x7 Civic Guidance grounded in TN charters'}</span>
          </div>

          {/* Chat Messages */}
          <div className="wa-chat-body">
            {messages.map((m, idx) => (
              <div key={idx} className={`wa-bubble ${m.sender === 'user' ? 'outgoing' : 'incoming'}`}>
                <div className="wa-bubble-text">{m.text}</div>
                <div className="wa-bubble-time">
                  <span>{m.time}</span>
                  {m.sender === 'user' && <CheckCheck size={13} color="#53bdeb" />}
                </div>
              </div>
            ))}

            {loading && (
              <div className="wa-bubble incoming">
                <div className="wa-typing-dots">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            <div ref={chatScrollRef} />
          </div>

          {/* Quick Suggestions Pills */}
          <div className="wa-quick-pills">
            {quickPills.map((pill, i) => (
              <button
                key={i}
                type="button"
                className="wa-pill"
                onClick={() => handleSend(pill.query)}
              >
                {pill.label}
              </button>
            ))}
          </div>

          {/* Message Input Box */}
          <form
            className="wa-input-row"
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <input
              type="text"
              className="wa-input-field"
              placeholder={language === 'ta' ? 'கேள்வியை தட்டச்சு செய்யவும்...' : 'Type your question...'}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
            <button
              type="submit"
              className="wa-send-btn"
              disabled={!inputText.trim() || loading}
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

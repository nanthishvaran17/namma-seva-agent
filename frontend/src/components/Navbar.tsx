import React from 'react';
import { ShieldCheck, MessageSquare, Compass, CheckSquare, Smartphone, UserCheck, LogOut, Lock } from 'lucide-react';
import type { UserProfile } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  language: string;
  setLanguage: (lang: string) => void;
  user: UserProfile | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  language,
  setLanguage,
  user,
  onOpenAuth,
  onLogout,
}) => {
  return (
    <header className="header-bar">
      <div className="header-inner">
        <div className="logo-area" onClick={() => setActiveTab('home')}>
          <div className="logo-badge">
            <span>நம்ம சேவை</span>
          </div>
          <div>
            <div className="logo-text-title">Namma Seva Agent</div>
            <div className="logo-text-subtitle">
              {language === 'ta'
                ? 'தமிழ்நாடு அரசு சேவைகளுக்கான AI வழிகாட்டி'
                : 'Tamil Nadu Unified AI Civic Assistant'}
            </div>
          </div>
        </div>

        <nav className="nav-links">
          <button
            className={`nav-btn ${activeTab === 'home' ? 'active' : ''}`}
            onClick={() => setActiveTab('home')}
          >
            <Compass size={17} />
            <span>{language === 'ta' ? 'முகப்பு' : 'Home'}</span>
          </button>

          <button
            className={`nav-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={17} />
            <span>{language === 'ta' ? 'AI உதவி' : 'AI Assistant'}</span>
          </button>

          <button
            className={`nav-btn ${activeTab === 'services' ? 'active' : ''}`}
            onClick={() => setActiveTab('services')}
          >
            <ShieldCheck size={17} />
            <span>{language === 'ta' ? 'சேவைகள்' : 'Services'}</span>
          </button>

          <button
            className={`nav-btn ${activeTab === 'tasks' ? 'active' : ''}`}
            onClick={() => {
              if (!user) {
                onOpenAuth();
              } else {
                setActiveTab('tasks');
              }
            }}
          >
            <CheckSquare size={17} />
            <span>{language === 'ta' ? 'என் பணிகள்' : 'My Tasks'}</span>
          </button>

          <button
            className={`nav-btn ${activeTab === 'whatsapp' ? 'active' : ''}`}
            onClick={() => setActiveTab('whatsapp')}
          >
            <Smartphone size={17} />
            <span>WhatsApp</span>
          </button>

          {user?.role === 'ADMIN' && (
            <button
              className={`nav-btn ${activeTab === 'admin' ? 'active' : ''}`}
              onClick={() => setActiveTab('admin')}
            >
              <Lock size={17} />
              <span>Admin</span>
            </button>
          )}

          {/* Language Switcher */}
          <div className="lang-selector">
            <button
              className={`lang-btn ${language === 'ta' ? 'active' : ''}`}
              onClick={() => setLanguage('ta')}
            >
              தமிழ்
            </button>
            <button
              className={`lang-btn ${language === 'tanglish' ? 'active' : ''}`}
              onClick={() => setLanguage('tanglish')}
            >
              Tanglish
            </button>
            <button
              className={`lang-btn ${language === 'en' ? 'active' : ''}`}
              onClick={() => setLanguage('en')}
            >
              English
            </button>
          </div>

          {/* User Auth */}
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary)' }}>
                {user.full_name}
              </span>
              <button
                className="nav-btn"
                style={{ padding: '0.4rem', color: '#dc2626' }}
                onClick={onLogout}
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button className="btn-primary" onClick={onOpenAuth} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
              <UserCheck size={15} />
              <span>{language === 'ta' ? 'உள்நுழைக' : 'Sign In'}</span>
            </button>
          )}
        </nav>
      </div>
    </header>
  );
};

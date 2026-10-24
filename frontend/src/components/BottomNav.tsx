import React from 'react';
import { Compass, MessageSquare, ShieldCheck, CheckSquare } from 'lucide-react';
import type { UserProfile } from '../types';

interface BottomNavProps {
  activeTab: string;
  setActiveTab: (tab: any) => void;
  language: string;
  user: UserProfile | null;
  onOpenAuth: () => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  activeTab,
  setActiveTab,
  language,
  user,
  onOpenAuth
}) => {
  return (
    <div className="mobile-bottom-nav">
      <button
        className={`bottom-nav-item ${activeTab === 'home' ? 'active' : ''}`}
        onClick={() => setActiveTab('home')}
      >
        <Compass size={20} />
        <span>{language === 'ta' ? 'முகப்பு' : 'Home'}</span>
      </button>

      <button
        className={`bottom-nav-item ${activeTab === 'services' ? 'active' : ''}`}
        onClick={() => setActiveTab('services')}
      >
        <ShieldCheck size={20} />
        <span>{language === 'ta' ? 'சேவைகள்' : 'Services'}</span>
      </button>

      {/* Central AI Chat action with glowing bubble */}
      <button
        className={`bottom-nav-item center-chat-btn ${activeTab === 'chat' ? 'active' : ''}`}
        onClick={() => setActiveTab('chat')}
      >
        <div className="center-chat-icon">
          <MessageSquare size={22} color="white" />
          <span className="pulse-ping" />
        </div>
        <span className="font-bold">{language === 'ta' ? 'AI உதவி' : 'AI Chat'}</span>
      </button>

      <button
        className={`bottom-nav-item ${activeTab === 'tasks' ? 'active' : ''}`}
        onClick={() => {
          if (!user) {
            onOpenAuth();
          } else {
            setActiveTab('tasks');
          }
        }}
      >
        <CheckSquare size={20} />
        <span>{language === 'ta' ? 'பணிகள்' : 'My Tasks'}</span>
      </button>
    </div>
  );
};

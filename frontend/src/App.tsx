import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HeroSearch } from './components/HeroSearch';
import { CategoryExplorer } from './components/CategoryExplorer';
import { TrustPrivacySection } from './components/TrustPrivacySection';
import { AssistantChat } from './components/AssistantChat';
import { ServicesDirectory } from './components/ServicesDirectory';
import { CitizenDashboard } from './components/CitizenDashboard';
import { AdminDashboard } from './components/AdminDashboard';
import { WhatsAppSimulator } from './components/WhatsAppSimulator';
import { AuthModal } from './components/AuthModal';
import { ApiClient } from './services/api';
import type { UserProfile } from './types';
import { ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'home' | 'chat' | 'services' | 'tasks' | 'whatsapp' | 'admin'>('home');
  const [language, setLanguage] = useState<string>('ta');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [pendingChatQuery, setPendingChatQuery] = useState<string | undefined>(undefined);
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);

  useEffect(() => {
    // Check existing auth
    if (ApiClient.getToken()) {
      ApiClient.getProfile()
        .then((profile) => setUser(profile))
        .catch(() => {
          ApiClient.setToken(null);
          setUser(null);
        });
    }
  }, []);

  const handleHeroSearch = (query: string) => {
    setPendingChatQuery(query);
    setActiveTab('chat');
  };

  const handleSelectCategory = (catId: string) => {
    setSelectedCategory(catId);
    setActiveTab('services');
  };

  const handleStartTask = async (serviceId: string) => {
    if (!user) {
      setAuthModalOpen(true);
      return;
    }
    try {
      await ApiClient.createTask(serviceId);
      setActiveTab('tasks');
    } catch (err: any) {
      alert(`Could not initiate task: ${err.message}`);
    }
  };

  const handleLogout = () => {
    ApiClient.setToken(null);
    setUser(null);
    setActiveTab('home');
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab as any}
        language={language}
        setLanguage={setLanguage}
        user={user}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      <main className="main-content">
        {activeTab === 'home' && (
          <>
            <HeroSearch language={language} onSearch={handleHeroSearch} />
            <CategoryExplorer language={language} onSelectCategory={handleSelectCategory} />
            <TrustPrivacySection language={language} />
          </>
        )}

        {activeTab === 'chat' && (
          <AssistantChat
            language={language}
            initialQuery={pendingChatQuery}
            onStartServiceTask={handleStartTask}
          />
        )}

        {activeTab === 'services' && (
          <ServicesDirectory
            language={language}
            initialCategory={selectedCategory}
            onStartTask={handleStartTask}
          />
        )}

        {activeTab === 'tasks' && user && (
          <CitizenDashboard
            language={language}
            user={user}
            onSelectService={() => setActiveTab('services')}
          />
        )}

        {activeTab === 'whatsapp' && (
          <WhatsAppSimulator />
        )}

        {activeTab === 'admin' && (
          <AdminDashboard />
        )}
      </main>

      {/* Footer */}
      <footer style={{ background: '#0a192f', color: '#94a3b8', padding: '2.5rem 1.5rem', marginTop: 'auto', borderTop: '1px solid #1e293b' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'white', fontWeight: 800, fontSize: '1.1rem', marginBottom: '0.25rem' }}>
              <ShieldCheck size={20} color="#ffb74d" />
              <span>நம்ம சேவை (Namma Seva Agent AI)</span>
            </div>
            <div style={{ fontSize: '0.8rem', maxWidth: '500px', lineHeight: '1.5' }}>
              Tamil Nadu's unified AI civic platform grounded in official Citizen Charters. An independent assistance technology developed in alignment with the DPDP Act 2023.
            </div>
          </div>

          <div style={{ fontSize: '0.82rem', textAlign: 'right' }}>
            <div>Emergency Helpline: <strong>1100 (CM Helpline)</strong></div>
            <div style={{ marginTop: '0.2rem', color: '#64748b' }}>e-Sevai Portal: tnesevai.tn.gov.in</div>
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(loggedUser) => setUser(loggedUser)}
      />
    </div>
  );
};

export default App;

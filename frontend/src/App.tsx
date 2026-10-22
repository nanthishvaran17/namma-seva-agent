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

        {activeTab === 'tasks' && (
          user ? (
            <CitizenDashboard
              language={language}
              user={user}
              onSelectService={() => setActiveTab('services')}
            />
          ) : (
            <div style={{ maxWidth: '600px', margin: '4rem auto', padding: '2.5rem', textAlign: 'center', background: 'white', borderRadius: '1rem', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(15, 52, 96, 0.08)' }}>
              <div style={{ display: 'inline-flex', padding: '1rem', borderRadius: '50%', background: '#f8fafc', marginBottom: '1rem' }}>
                <ShieldCheck size={40} color="#0f3460" />
              </div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#0f3460', marginBottom: '0.5rem' }}>
                {language === 'ta' ? 'விண்ணப்பங்களைக் கண்காணிக்க உள்நுழையவும்' : 'Sign In to Access Your Civic Tasks'}
              </h2>
              <p style={{ color: '#64748b', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: '1.6' }}>
                {language === 'ta'
                  ? 'உங்கள் சான்றிதழ் விண்ணப்ப நிலை, ஆவண சரிபார்ப்பு மற்றும் உடனடி நினைவூட்டல்களைப் பெற உள்நுழையவும்.'
                  : 'Log in to track certificate workflow progress, upload documents for verification, and download action plans.'}
              </p>
              <button
                className="btn btn-primary"
                onClick={() => setAuthModalOpen(true)}
                style={{ padding: '0.75rem 2.25rem', fontSize: '1rem', fontWeight: 600 }}
              >
                {language === 'ta' ? 'உள்நுழைக / பதிவு செய்க (Login)' : 'Sign In / Register'}
              </button>
            </div>
          )
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

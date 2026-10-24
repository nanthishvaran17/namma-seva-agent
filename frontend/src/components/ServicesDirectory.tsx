import React, { useState, useEffect } from 'react';
import { Search, ShieldCheck, Clock, ArrowRight, Layers, Award, X } from 'lucide-react';
import { ApiClient } from '../services/api';
import type { ServiceItem } from '../types';

interface ServicesDirectoryProps {
  language: string;
  initialCategory?: string;
  onStartTask: (serviceId: string) => void;
}

export const ServicesDirectory: React.FC<ServicesDirectoryProps> = ({
  language,
  initialCategory,
  onStartTask,
}) => {
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategory || '');
  const [selectedService, setSelectedService] = useState<ServiceItem | null>(null);

  useEffect(() => {
    loadServices();
  }, [selectedCategory]);

  const loadServices = async () => {
    try {
      const data = await ApiClient.getServices(searchQuery, selectedCategory || undefined);
      setServices(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadServices();
  };

  return (
    <div className="apple-services-section">
      <div style={{ marginBottom: '2.5rem' }}>
        <span className="apple-kicker">
          {language === 'ta' ? 'அதிகாரப்பூர்வ ஆவணங்கள்' : 'Verified Charters'}
        </span>
        <h2 className="apple-section-title">
          {language === 'ta' ? 'அரசு சேவைகள் வழிகாட்டி பட்டியல்' : 'Government Services Directory'}
        </h2>
        <p className="apple-section-desc">
          {language === 'ta'
            ? 'அனைத்து சேவைகளும் குடிமக்கள் சாசனம் மற்றும் அதிகாரப்பூர்வ அரசாணைகளின்படி சரிபார்க்கப்பட்டவை.'
            : 'All playbooks verified against official Tamil Nadu Government Citizen Charters and Gazette notifications.'}
        </p>
      </div>

      {/* Apple Spotlight Search and Category Bar */}
      <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.75rem', marginBottom: '2.5rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1', minWidth: '280px', position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '1.25rem', top: '50%', transform: 'translateY(-50%)', color: '#86868b' }} />
          <input
            type="text"
            placeholder={language === 'ta' ? 'சேவை பெயர் அல்லது துறை மூலம் தேடுக...' : 'Search by service name, keyword or department...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '0.85rem 1.25rem 0.85rem 3rem',
              borderRadius: '9999px',
              border: '1px solid rgba(0, 0, 0, 0.12)',
              outline: 'none',
              fontFamily: 'inherit',
              fontSize: '0.95rem',
              background: '#ffffff',
              boxShadow: '0 4px 14px rgba(0, 0, 0, 0.04)'
            }}
          />
        </div>

        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          style={{
            padding: '0.85rem 1.25rem',
            borderRadius: '9999px',
            border: '1px solid rgba(0, 0, 0, 0.12)',
            fontFamily: 'inherit',
            fontSize: '0.9rem',
            background: '#ffffff',
            color: '#1d1d1f',
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(0, 0, 0, 0.04)'
          }}
        >
          <option value="">{language === 'ta' ? 'அனைத்துப் பிரிவுகள் (All Categories)' : 'All Categories'}</option>
          <option value="certificates_revenue">வருவாய்ச் சான்றிதழ்கள் (Revenue)</option>
          <option value="scholarships_education">கல்வி & உதவித்தொகை (Scholarships)</option>
          <option value="welfare_social">சமூக நலன் (Social Welfare)</option>
          <option value="farmer_agriculture">வேளாண்மை (Agriculture)</option>
        </select>

        <button type="submit" className="apple-pill-btn primary">
          <span>{language === 'ta' ? 'தேடுக' : 'Search'}</span>
        </button>
      </form>

      {/* Services List Grid */}
      <div className="apple-cards-grid">
        {services.map((s) => (
          <div key={s.service_id} className="apple-card">
            <div className="apple-card-top">
              <div className="apple-squircle" style={{ background: 'linear-gradient(135deg, #0071e3 0%, #5856d6 100%)' }}>
                <Award size={24} color="white" />
              </div>

              <div className="apple-card-headings">
                <h3 className="apple-card-title">
                  {language === 'ta' ? s.name_ta : s.name_en}
                </h3>
                <span className="apple-card-subtitle">{s.department}</span>
              </div>

              <div className="apple-fee-pill">
                {s.fee?.is_free ? (language === 'ta' ? 'இலவசம்' : 'Free') : `₹${s.fee?.amount_inr}`}
              </div>
            </div>

            <p className="apple-card-desc">
              {language === 'ta' ? s.description_ta : s.description_en}
            </p>

            {s.dependencies && s.dependencies.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: '#b45309', background: 'rgba(255, 149, 0, 0.08)', padding: '0.4rem 0.75rem', borderRadius: '8px', marginBottom: '1.25rem' }}>
                <Layers size={14} />
                <span>Prerequisites: {s.dependencies.join(', ')}</span>
              </div>
            )}

            <div className="apple-card-bottom">
              <div className="apple-timeline">
                <Clock size={14} className="apple-clock-icon" />
                <span>{s.processing_time?.working_days} {language === 'ta' ? 'நாட்கள்' : 'days turnaround'}</span>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  className="apple-pill-btn secondary"
                  onClick={() => setSelectedService(s)}
                >
                  <span>{language === 'ta' ? 'விவரம்' : 'Details'}</span>
                </button>
                <button
                  type="button"
                  className="apple-pill-btn primary"
                  onClick={() => onStartTask(s.service_id)}
                >
                  <span>{language === 'ta' ? 'விண்ணப்பிக்க' : 'Apply'}</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Service Detail Modal — Apple Sheet Style */}
      {selectedService && (
        <div className="apple-sheet-backdrop" onClick={() => setSelectedService(null)}>
          <div className="apple-sheet-card" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '580px', textAlign: 'left' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <h3 className="apple-sheet-title" style={{ textAlign: 'left' }}>
                  {language === 'ta' ? selectedService.name_ta : selectedService.name_en}
                </h3>
                <span className="apple-card-subtitle">{selectedService.department}</span>
              </div>
              <button
                className="apple-icon-btn"
                onClick={() => setSelectedService(null)}
                style={{ width: '32px', height: '32px' }}
              >
                <X size={16} />
              </button>
            </div>

            <p className="apple-card-desc" style={{ marginBottom: '1.5rem' }}>
              {language === 'ta' ? selectedService.description_ta : selectedService.description_en}
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: '#f5f5f7', padding: '1.25rem', borderRadius: '18px', marginBottom: '1.5rem' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#86868b', fontWeight: 600 }}>Statutory Fee</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0071e3', marginTop: '2px' }}>
                  {selectedService.fee?.is_free ? 'Free (₹0)' : `₹${selectedService.fee?.amount_inr}`}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#86868b', fontWeight: 600 }}>Processing Timeline</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#1d1d1f', marginTop: '2px' }}>
                  {selectedService.processing_time?.working_days} Days
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                className="apple-pill-btn secondary"
                onClick={() => setSelectedService(null)}
              >
                {language === 'ta' ? 'மூடுக' : 'Close'}
              </button>
              <button
                className="apple-pill-btn primary"
                onClick={() => {
                  const id = selectedService.service_id;
                  setSelectedService(null);
                  onStartTask(id);
                }}
              >
                {language === 'ta' ? 'விண்ணப்பிக்க தொடங்குக' : 'Start Application'}
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

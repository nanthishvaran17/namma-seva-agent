import React, { useState, useEffect } from 'react';
import { Search, ShieldCheck, Clock, ExternalLink, ArrowRight, FileCheck, Layers } from 'lucide-react';
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
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadServices();
  }, [selectedCategory]);

  const loadServices = async () => {
    setLoading(true);
    try {
      const data = await ApiClient.getServices(searchQuery, selectedCategory || undefined);
      setServices(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadServices();
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 className="section-title" style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
          {language === 'ta' ? 'அரசு சேவைகள் வழிகாட்டி பட்டியல்' : 'Verified Government Services Directory'}
        </h2>
        <p style={{ color: 'var(--text-muted)' }}>
          {language === 'ta'
            ? 'அனைத்து சேவைகளும் குடிமக்கள் சாசனம் மற்றும் அதிகாரப்பூர்வ அரசாணைகளின்படி சரிபார்க்கப்பட்டவை.'
            : 'All playbooks verified against official Tamil Nadu Government Citizen Charters and Gazette notifications.'}
        </p>
      </div>

      {/* Filter and Search Bar */}
      <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1', minWidth: '260px', position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder={language === 'ta' ? 'சேவை பெயர் அல்லது துறை மூலம் தேடுக...' : 'Search by service name, keyword or department...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ width: '100%', padding: '0.75rem 1rem 0.75rem 2.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', outline: 'none', fontFamily: 'inherit' }}
          />
        </div>

        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          style={{ padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontFamily: 'inherit', background: 'white', color: 'var(--text-main)', cursor: 'pointer' }}
        >
          <option value="">{language === 'ta' ? 'அனைத்துப் பிரிவுகள் (All Categories)' : 'All Categories'}</option>
          <option value="certificates_revenue">வருவாய்ச் சான்றிதழ்கள் (Revenue)</option>
          <option value="scholarships_education">கல்வி & உதவித்தொகை (Scholarships)</option>
          <option value="welfare_social">சமூக நலன் (Social Welfare)</option>
          <option value="farmer_agriculture">வேளாண்மை (Agriculture)</option>
        </select>

        <button type="submit" className="btn-primary">
          <span>{language === 'ta' ? 'தேடுக' : 'Search'}</span>
        </button>
      </form>

      {/* Services List Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.25rem' }}>
        {services.map((s) => (
          <div
            key={s.service_id}
            style={{
              background: 'white',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: 'var(--shadow-sm)',
              transition: 'all 0.15s ease'
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <span className="verified-tag">
                  <ShieldCheck size={12} />
                  <span>{s.verification_status}</span>
                </span>
                <span className="fee-badge">
                  {s.fee?.is_free ? 'இலவசம் (Free)' : `₹${s.fee?.amount_inr}`}
                </span>
              </div>

              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--primary)', marginBottom: '0.35rem' }}>
                {language === 'ta' ? s.name_ta : s.name_en}
              </h3>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '0.75rem' }}>
                {s.department}
              </div>

              <p style={{ fontSize: '0.86rem', color: '#475569', lineHeight: '1.5', marginBottom: '1rem' }}>
                {language === 'ta' ? s.description_ta : s.description_en}
              </p>

              {/* Dependencies badge if any */}
              {s.dependencies && s.dependencies.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: '#b45309', background: '#fef3c7', padding: '0.3rem 0.6rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem' }}>
                  <Layers size={14} />
                  <span>Prerequisites: {s.dependencies.join(', ')}</span>
                </div>
              )}
            </div>

            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <Clock size={14} />
                <span>{s.processing_time?.working_days} days turnaround</span>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                  onClick={() => setSelectedService(s)}
                >
                  <span>Details</span>
                </button>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
                  onClick={() => onStartTask(s.service_id)}
                >
                  <span>Apply</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Service Detail Modal */}
      {selectedService && (
        <div className="modal-overlay" onClick={() => setSelectedService(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--primary)' }}>
                  {language === 'ta' ? selectedService.name_ta : selectedService.name_en}
                </h3>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{selectedService.department}</div>
              </div>
              <span className="verified-tag">
                <ShieldCheck size={14} />
                <span>VERIFIED</span>
              </span>
            </div>

            <p style={{ fontSize: '0.92rem', color: '#334155', lineHeight: '1.6', marginBottom: '1.25rem' }}>
              {language === 'ta' ? selectedService.description_ta : selectedService.description_en}
            </p>

            {/* Official Fee & Processing */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: '#f8fafc', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', border: '1px solid var(--border-color)' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Statutory Portal Fee</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#059669' }}>
                  {selectedService.fee?.is_free ? 'Free (₹0)' : `₹${selectedService.fee?.amount_inr}`}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{selectedService.fee?.verified_description}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Processing Timeline</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--primary)' }}>
                  {selectedService.processing_time?.working_days} Working Days
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  {language === 'ta' ? selectedService.processing_time?.description_ta : selectedService.processing_time?.description_en}
                </div>
              </div>
            </div>

            {/* Prerequisites DAG */}
            {selectedService.dependencies && selectedService.dependencies.length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.5rem' }}>
                  Prerequisite Certificates Required:
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {selectedService.dependencies.map((dep, dIdx) => (
                    <span key={dIdx} style={{ background: '#fef3c7', color: '#92400e', padding: '0.3rem 0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.82rem', fontWeight: 600 }}>
                      {dep.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Required Documents */}
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.5rem' }}>
                Mandatory Supporting Documents:
              </h4>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.88rem', color: '#334155', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {selectedService.required_documents?.map((doc, docIdx) => (
                  <li key={docIdx}>
                    <strong>{language === 'ta' ? doc.name_ta : doc.name_en}</strong>
                    {doc.description && <span style={{ color: 'var(--text-muted)', marginLeft: '4px' }}>— {doc.description}</span>}
                  </li>
                ))}
              </ul>
            </div>

            {/* Official Sources */}
            <div style={{ marginBottom: '1.75rem' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.5rem' }}>
                Official Government Sources:
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {selectedService.official_sources?.map((src, sIdx) => (
                  <a key={sIdx} href={src.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.82rem', color: '#0284c7', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                    <ExternalLink size={13} />
                    <span>{src.title} ({src.publisher})</span>
                  </a>
                ))}
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <button type="button" className="btn-secondary" onClick={() => setSelectedService(null)}>
                Close
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={() => {
                  const sId = selectedService.service_id;
                  setSelectedService(null);
                  onStartTask(sId);
                }}
              >
                <span>Start Assisted Application</span>
                <ArrowRight size={15} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

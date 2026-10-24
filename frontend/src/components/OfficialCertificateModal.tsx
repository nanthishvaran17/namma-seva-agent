import React, { useState } from 'react';
import {
  X,
  Copy,
  Check,
  AlertTriangle,
  ExternalLink,
  FileCheck,
  ClipboardList,
  Clock,
  Building,
  CreditCard
} from 'lucide-react';

interface OfficialCertificateModalProps {
  task: any;
  user: any;
  language: string;
  onClose: () => void;
  onTaskUpdated?: () => void;
}

export const OfficialCertificateModal: React.FC<OfficialCertificateModalProps> = ({
  task,
  user,
  language,
  onClose,
}) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const getServiceMetadata = () => {
    switch (task.service_id) {
      case 'community_certificate':
        return {
          serviceNameTa: 'சாதிச் சான்றிதழ் (Community Certificate)',
          serviceNameEn: 'Community / Caste Certificate',
          deptTa: 'வருவாய் மற்றும் பேரிடர் மேலாண்மைத் துறை',
          deptEn: 'Revenue & Disaster Management Department',
          portalUrl: 'https://www.tnesevai.tn.gov.in',
          fee: '₹60',
          timeline: '15 working days',
          checklist: [
            'Applicant Passport Size Photo',
            'Address Proof (Smart Ration Card / Aadhaar)',
            'Parent / Sibling Community Certificate Proof',
            'Self Declaration Form'
          ]
        };
      case 'income_certificate':
        return {
          serviceNameTa: 'வருமானச் சான்றிதழ் (Income Certificate)',
          serviceNameEn: 'Annual Family Income Certificate',
          deptTa: 'வருவாய் மற்றும் பேரிடர் மேலாண்மைத் துறை',
          deptEn: 'Revenue & Disaster Management Department',
          portalUrl: 'https://www.tnesevai.tn.gov.in',
          fee: '₹60',
          timeline: '15 working days',
          checklist: [
            'Applicant / Family Head Smart Ration Card',
            'Salary Certificate / Income Proof / Self Affidavit',
            'Aadhaar Card'
          ]
        };
      case 'first_graduate_certificate':
        return {
          serviceNameTa: 'முதல் தலைமுறை பட்டதாரி சான்றிதழ் (First Graduate)',
          serviceNameEn: 'First Graduate Certificate (Tuition Fee Concession)',
          deptTa: 'உயர் கல்வி மற்றும் வருவாய்த் துறை',
          deptEn: 'Higher Education & Revenue Administration',
          portalUrl: 'https://www.tnesevai.tn.gov.in',
          fee: '₹60',
          timeline: '15 working days',
          checklist: [
            'Nativity Certificate (Prerequisite)',
            'Smart Ration Card of Family',
            'School Transfer Certificates (TC) of Parents & Siblings',
            'Prescribed Joint Declaration Signed by Applicant & Parents'
          ]
        };
      case 'post_matric_scholarship':
        return {
          serviceNameTa: 'போஸ்ட்-மெட்ரிக் கல்வி உதவித்தொகை (Post-Matric Scholarship)',
          serviceNameEn: 'Tamil Nadu Post-Matric Scholarship Scheme',
          deptTa: 'ஆதிதிராவிடர், பழங்குடியினர் மற்றும் பிற்படுத்தப்பட்டோர் நலத்துறை',
          deptEn: 'Adi Dravidar and Tribal Welfare & BC/MBC/Minorities Welfare Dept',
          portalUrl: 'https://scholarships.gov.in',
          fee: '₹0 (Free of Cost)',
          timeline: 'Annual scheme cycle',
          checklist: [
            'Verified Community Certificate (Prerequisite)',
            'Verified Income Certificate (Prerequisite)',
            'Verified Nativity Certificate (Prerequisite)',
            'College Admission / Bonafide Certificate & Fee Receipt',
            'Aadhaar-seeded Bank Account Passbook'
          ]
        };
      case 'nativity_certificate':
        return {
          serviceNameTa: 'இருப்பிடச் சான்றிதழ் (Nativity Certificate)',
          serviceNameEn: 'Nativity / Domicile Certificate',
          deptTa: 'வருவாய் மற்றும் பேரிடர் மேலாண்மைத் துறை',
          deptEn: 'Revenue & Disaster Management Department',
          portalUrl: 'https://www.tnesevai.tn.gov.in',
          fee: '₹60',
          timeline: '15 working days',
          checklist: [
            'Birth Certificate / Proof of Birth in Tamil Nadu',
            'School Transfer Certificate (5+ Years studied in TN)',
            'Parent Residence Proof in TN (10+ Years)',
            'Smart Family Card / Ration Card'
          ]
        };
      default:
        return {
          serviceNameTa: 'அரசு சேவை விண்ணப்பம்',
          serviceNameEn: 'Government Service Application',
          deptTa: 'தமிழ்நாடு அரசு துறைகள்',
          deptEn: 'Government of Tamil Nadu',
          portalUrl: 'https://www.tnesevai.tn.gov.in',
          fee: '₹60',
          timeline: '15 working days',
          checklist: ['Identity Proof', 'Address Proof', 'Application Specific Proofs']
        };
    }
  };

  const meta = getServiceMetadata();

  const handleCopy = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const prefillFields = [
    { labelTa: 'விண்ணப்பதாரர் பெயர்', labelEn: 'Applicant Name', key: 'name', value: user?.full_name || 'Citizen Applicant' },
    { labelTa: 'கைபேசி எண்', labelEn: 'Mobile Number', key: 'mobile', value: user?.phone_number || '9876543210' },
    { labelTa: 'மின்னஞ்சல்', labelEn: 'Email Address', key: 'email', value: user?.email || 'citizen@example.com' },
    { labelTa: 'மாநிலம்', labelEn: 'State', key: 'state', value: 'Tamil Nadu' },
    { labelTa: 'மாவட்டம்', labelEn: 'District', key: 'district', value: user?.district || 'Coimbatore' },
    { labelTa: 'சேவை அடையாளம்', labelEn: 'Service Code', key: 'service_id', value: task.service_id },
    { labelTa: 'அரசு கட்டணம்', labelEn: 'Statutory Fee', key: 'fee', value: meta.fee },
    { labelTa: 'வழங்கும் காலம்', labelEn: 'Delivery Timeline', key: 'timeline', value: meta.timeline }
  ];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '1rem'
      }}
    >
      <div
        style={{
          background: '#ffffff',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '780px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          overflow: 'hidden'
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#0f3460',
            color: '#ffffff'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ClipboardList size={24} style={{ color: '#38bdf8' }} />
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>
                {language === 'ta' ? meta.serviceNameTa : meta.serviceNameEn}
              </h2>
              <p style={{ margin: '2px 0 0 0', fontSize: '0.82rem', color: '#94a3b8' }}>
                {language === 'ta' ? 'அதிகாரப்பூர்வ போர்ட்டல் விண்ணப்ப வழிகாட்டி & சரிபார்ப்புப் பட்டியல்' : 'Official Portal Pre-fill Sheet & Verified Checklist'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#ffffff',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
          {/* Prominent Legal Disclaimer Banner */}
          <div
            style={{
              background: '#fef3c7',
              border: '1px solid #f59e0b',
              borderRadius: '10px',
              padding: '1rem 1.25rem',
              marginBottom: '1.5rem',
              display: 'flex',
              gap: '12px',
              alignItems: 'flex-start'
            }}
          >
            <AlertTriangle size={24} style={{ color: '#b45309', flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 800, color: '#92400e', fontSize: '0.95rem' }}>
                {language === 'ta'
                  ? 'முக்கிய அறிவிப்பு: இது அதிகாரப்பூர்வ அரசு சான்றிதழ் அல்ல'
                  : 'IMPORTANT NOTICE: THIS IS NOT AN OFFICIAL GOVERNMENT CERTIFICATE'}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#78350f', marginTop: '0.3rem', lineHeight: '1.5' }}>
                {language === 'ta'
                  ? 'இது உங்கள் அதிகாரப்பூர்வ இ-சேவை / அரசு போர்ட்டலில் விண்ணப்பிக்க உதவும் முன்-நிரப்பு வழிகாட்டித் தாள் மட்டுமே. அதிகாரப்பூர்வ சான்றிதழ்களை அரசு வருவாய்த் துறை அதிகாரிகள் மட்டுமே நேரில்/கள ஆய்வு செய்து வழங்க முடியும். மனித மேற்பார்வையின்றி எவ்வித விண்ணப்பமும் தன்னிச்சையாக சமர்ப்பிக்கப்படாது.'
                  : 'This is an application pre-fill checklist generated by Namma Seva Agent to assist you when applying on the official government portal. Official certificates are exclusively issued by authorized Government of Tamil Nadu revenue officials after statutory scrutiny. Autonomous submission without human review is strictly prohibited.'}
              </div>
            </div>
          </div>

          {/* Quick Service Overview Badges */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '0.75rem',
              marginBottom: '1.5rem'
            }}
          >
            <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Building size={20} style={{ color: '#0284c7' }} />
              <div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>{language === 'ta' ? 'துறை' : 'Department'}</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b' }}>{language === 'ta' ? meta.deptTa : meta.deptEn}</div>
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CreditCard size={20} style={{ color: '#16a34a' }} />
              <div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>{language === 'ta' ? 'அரசு கட்டணம்' : 'Statutory Fee'}</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#16a34a' }}>{meta.fee}</div>
              </div>
            </div>

            <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Clock size={20} style={{ color: '#d97706' }} />
              <div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>{language === 'ta' ? 'வழங்கும் காலம்' : 'SLA Timeline'}</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#1e293b' }}>{meta.timeline}</div>
              </div>
            </div>
          </div>

          {/* Section 1: Copyable Pre-fill Details */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.98rem', fontWeight: 700, margin: '0 0 0.75rem 0', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ClipboardList size={18} style={{ color: '#0284c7' }} />
              <span>{language === 'ta' ? '1. போர்ட்டலில் நகலெடுத்து நிரப்ப வேண்டிய விவரங்கள்' : '1. Copyable Pre-fill Details for Portal'}</span>
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
              {prefillFields.map(f => (
                <div
                  key={f.key}
                  style={{
                    background: '#f8fafc',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    border: '1px solid #e2e8f0',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '4px'
                  }}
                >
                  <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>
                    {language === 'ta' ? f.labelTa : f.labelEn}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {f.value}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCopy(f.key, f.value)}
                      title="Copy to clipboard"
                      style={{
                        background: copiedKey === f.key ? '#dcfce7' : '#ffffff',
                        border: '1px solid #cbd5e1',
                        borderRadius: '6px',
                        padding: '4px 8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '0.75rem',
                        color: copiedKey === f.key ? '#166534' : '#475569'
                      }}
                    >
                      {copiedKey === f.key ? (
                        <>
                          <Check size={12} />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 2: Verified Document Checklist */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '0.98rem', fontWeight: 700, margin: '0 0 0.75rem 0', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FileCheck size={18} style={{ color: '#16a34a' }} />
              <span>{language === 'ta' ? '2. தேவைப்படும் ஆவணங்களின் சரிபார்ப்புப் பட்டியல்' : '2. Verified Document Checklist'}</span>
            </h3>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '0.75rem 1rem' }}>
              {meta.checklist.map((item, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '0.5rem 0',
                    borderBottom: idx < meta.checklist.length - 1 ? '1px solid #f1f5f9' : 'none',
                    fontSize: '0.88rem',
                    color: '#334155'
                  }}
                >
                  <div
                    style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      background: '#dcfce7',
                      color: '#166534',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      flexShrink: 0
                    }}
                  >
                    ✓
                  </div>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 3: Official Citizen Portal Entry Link */}
          <div
            style={{
              background: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: '10px',
              padding: '1.25rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px'
            }}
          >
            <div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#1e40af' }}>
                {language === 'ta' ? 'அதிகாரப்பூர்வ அரசு இணையதளத்தில் விண்ணப்பிக்கவும்' : 'Apply on the Official Government Portal'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#3b82f6', marginTop: '2px' }}>
                {meta.portalUrl}
              </div>
            </div>

            <a
              href={meta.portalUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                background: '#0284c7',
                color: '#ffffff',
                textDecoration: 'none',
                borderRadius: '8px',
                padding: '0.65rem 1.25rem',
                fontSize: '0.88rem',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <span>{language === 'ta' ? 'அரசு போர்ட்டலைத் திற (Portal)' : 'Open Official Portal'}</span>
              <ExternalLink size={16} />
            </a>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '10px',
            backgroundColor: '#f8fafc'
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              background: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: '8px',
              padding: '0.6rem 1.25rem',
              fontSize: '0.88rem',
              fontWeight: 600,
              color: '#475569',
              cursor: 'pointer'
            }}
          >
            {language === 'ta' ? 'மூடு (Close)' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};

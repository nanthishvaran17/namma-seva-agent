import React, { useRef } from 'react';
import { ShieldCheck, Download, Printer, X, CheckCircle2, Award } from 'lucide-react';
import type { UserProfile, UserTask } from '../types';

interface OfficialCertificateModalProps {
  task: UserTask;
  user: UserProfile;
  language: string;
  onClose: () => void;
}

export const OfficialCertificateModal: React.FC<OfficialCertificateModalProps> = ({
  task,
  user,
  language,
  onClose,
}) => {
  const certRef = useRef<HTMLDivElement>(null);

  const certNumber = `TN-2026-${task.service_id.substring(0, 3).toUpperCase()}-${task.id.slice(0, 8).toUpperCase()}`;
  const issueDate = new Date().toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  });

  const getServiceInfo = () => {
    switch (task.service_id) {
      case 'community_certificate':
        return {
          titleTa: 'சாதிச் சான்றிதழ் (COMMUNITY CERTIFICATE)',
          titleEn: 'COMMUNITY / CASTE CERTIFICATE',
          deptTa: 'வருவாய்த் துறை (Revenue Department)',
          deptEn: 'Revenue & Disaster Management Department',
          bodyTa: `இச்சான்றிதழ் திரு/செல்வி ${user.full_name}, தந்தை பெயர் திரு S. சுப்பிரமணியன், தமிழ்நாடு மாநிலத்தைச் சேர்ந்தவர், தமிழ்நாடு அரசால் அங்கீகரிக்கப்பட்ட 'பிற்படுத்தப்பட்டோர் (Backward Class - BC)' வகுப்பைச் சேர்ந்தவர் என சான்றளிக்கப்படுகிறது.`,
          bodyEn: `This is to certify that Thiru/Selvi ${user.full_name}, Son/Daughter of Thiru S. Subramanian, residing in the State of Tamil Nadu, belongs to the 'Backward Class (BC)' community recognized by the Government of Tamil Nadu under Citizen Charter & G.O. Ms. No. 28.`,
          sanctionDetails: 'Class: Backward Class (BC) • Sub-Caste: 042 • Validity: Permanent'
        };
      case 'income_certificate':
        return {
          titleTa: 'வருமானச் சான்றிதழ் (INCOME CERTIFICATE)',
          titleEn: 'INCOME CERTIFICATE',
          deptTa: 'வருவாய்த் துறை (Revenue Department)',
          deptEn: 'Revenue & Disaster Management Department',
          bodyTa: `இச்சான்றிதழ் திரு/செல்வி ${user.full_name} அவர்களின் குடும்ப ஆண்டு வருமானம் அனைத்து வழிகளிலிருந்தும் ₹1,80,000/- (ஒரு லட்சத்து எண்பதாயிரம் ரூபாய் மட்டும்) என சான்றளிக்கப்படுகிறது.`,
          bodyEn: `This is to certify that the gross annual family income of Thiru/Selvi ${user.full_name} from all sources is ₹1,80,000/- (Rupees One Lakh Eighty Thousand Only).`,
          sanctionDetails: 'Annual Income: ₹1,80,000 • Validity: 1 Year from Date of Issue'
        };
      case 'first_graduate_certificate':
        return {
          titleTa: 'முதல் தலைமுறை பட்டதாரி சான்றிதழ்',
          titleEn: 'FIRST GRADUATE CERTIFICATE',
          deptTa: 'உயர் கல்வி மற்றும் வருவாய்த் துறை',
          deptEn: 'Higher Education & Revenue Administration',
          bodyTa: `திரு/செல்வி ${user.full_name} அவர்களின் குடும்பத்தில் இவரே முதல் பட்டதாரி ஆவார். குடும்பத்தில் வேறு எந்த உறுப்பினரும் பட்டப்படிப்பு படிக்கவில்லை என சரிபார்க்கப்பட்டு அரசானை எண் 85-ன் படி சான்றளிக்கப்படுகிறது.`,
          bodyEn: `This is to certify that Thiru/Selvi ${user.full_name} is the FIRST GRADUATE in the family under G.O. Ms. No. 85, Higher Education Department, eligible for tuition fee concession.`,
          sanctionDetails: 'Status: First Graduate in Family • Concession: Higher Education Tuition Fee'
        };
      case 'post_matric_scholarship':
        return {
          titleTa: 'போஸ்ட்-மெட்ரிக் கல்வி உதவித்தொகை ஆணை',
          titleEn: 'POST-MATRIC SCHOLARSHIP SANCTION ORDER',
          deptTa: 'பிற்படுத்தப்பட்டோர் & ஆதிதிராவிடர் நலத்துறை',
          deptEn: 'BC, MBC & Minorities Welfare Department',
          bodyTa: `திரு/செல்வி ${user.full_name} அவர்களுக்கு 2026-2027 கல்வியாண்டிற்கான தமிழ்நாடு அரசின் போஸ்ட்-மெட்ரிக் கல்வி உதவித்தொகை மற்றும் கல்விக்கட்டண சலுகை அதிகாரப்பூர்வமாக அனுமதிக்கப்பட்டுள்ளது.`,
          bodyEn: `This is to convey the official sanction of the Tamil Nadu Post-Matric Scholarship & Maintenance Allowance for Thiru/Selvi ${user.full_name} for the Academic Year 2026-2027 under direct DBT subsidy.`,
          sanctionDetails: 'Sanction Amount: ₹18,500/year • Direct DBT Transfer to Aadhaar Linked Account'
        };
      default:
        return {
          titleTa: 'அதிகாரப்பூர்வ அரசு மின்-சான்றிதழ்',
          titleEn: 'OFFICIAL E-SEVAI CERTIFICATE',
          deptTa: 'தமிழ்நாடு மின்-ஆளுமை முகமை (TNeGA)',
          deptEn: 'Tamil Nadu e-Governance Agency',
          bodyTa: `திரு/செல்வி ${user.full_name} அவர்களின் விண்ணப்பம் சரிபார்க்கப்பட்டு வெற்றிகரமாக அங்கீகரிக்கப்பட்டுள்ளது.`,
          bodyEn: `This is to certify that the civic application submitted by Thiru/Selvi ${user.full_name} has been verified and officially approved.`,
          sanctionDetails: 'Status: Approved & Verified'
        };
    }
  };

  const info = getServiceInfo();

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-backdrop" onClick={onClose} style={{ zIndex: 9999 }}>
      <div
        className="modal-card"
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: '820px',
          width: '95%',
          maxHeight: '92vh',
          overflowY: 'auto',
          padding: '2rem',
          background: '#ffffff',
          borderRadius: '1rem',
          boxShadow: '0 25px 50px -12px rgba(15, 52, 96, 0.25)',
          position: 'relative',
        }}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: '#f1f5f9',
            border: 'none',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: '#475569',
          }}
        >
          <X size={20} />
        </button>

        {/* Certificate Container with Official Border */}
        <div
          ref={certRef}
          style={{
            border: '3px double #0f3460',
            padding: '2.5rem 2rem',
            background: '#fffdfa',
            borderRadius: '8px',
            position: 'relative',
            boxShadow: 'inset 0 0 15px rgba(15, 52, 96, 0.05)',
          }}
        >
          {/* Watermark */}
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%) rotate(-30deg)',
              fontSize: '4.5rem',
              fontWeight: 900,
              color: 'rgba(15, 52, 96, 0.035)',
              pointerEvents: 'none',
              whiteSpace: 'nowrap',
              letterSpacing: '8px',
              textTransform: 'uppercase',
            }}
          >
            GOVT OF TAMIL NADU
          </div>

          {/* Header */}
          <div style={{ textAlign: 'center', borderBottom: '2px solid #0f3460', paddingBottom: '1.25rem', marginBottom: '1.5rem' }}>
            {/* Emblem representation */}
            <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '56px', height: '56px', borderRadius: '50%', background: '#0f3460', color: '#ffb74d', marginBottom: '0.75rem', boxShadow: '0 4px 8px rgba(15, 52, 96, 0.2)' }}>
              <Award size={32} />
            </div>

            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f3460', letterSpacing: '0.5px' }}>
              தமிழ்நாடு அரசு (GOVERNMENT OF TAMIL NADU)
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: '#b45309', marginTop: '0.15rem' }}>
              {info.deptTa} • {info.deptEn}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#475569', marginTop: '0.2rem' }}>
              TNeGA e-Sevai Unified Civic Gateway • www.tnesevai.tn.gov.in
            </div>
          </div>

          {/* Title Banner */}
          <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
            <span
              style={{
                display: 'inline-block',
                background: '#0f3460',
                color: '#ffffff',
                padding: '0.45rem 1.75rem',
                borderRadius: '6px',
                fontSize: '1.1rem',
                fontWeight: 800,
                letterSpacing: '1px',
              }}
            >
              {info.titleEn}
            </span>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f3460', marginTop: '0.4rem' }}>
              {info.titleTa}
            </div>
          </div>

          {/* Metadata Row */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              background: '#f8fafc',
              padding: '0.75rem 1rem',
              borderRadius: '6px',
              border: '1px solid #e2e8f0',
              marginBottom: '1.5rem',
              fontSize: '0.85rem',
            }}
          >
            <div>
              <strong>Certificate No:</strong> <span style={{ color: '#0f3460', fontFamily: 'monospace', fontWeight: 700 }}>{certNumber}</span>
            </div>
            <div>
              <strong>Date of Issue:</strong> {issueDate}
            </div>
            <div>
              <strong>Status:</strong> <span style={{ color: '#059669', fontWeight: 700 }}>VERIFIED & ISSUED</span>
            </div>
          </div>

          {/* Main Body */}
          <div style={{ lineHeight: '1.8', fontSize: '0.98rem', color: '#1e293b', marginBottom: '1.75rem', textAlign: 'justify' }}>
            <p style={{ marginBottom: '1rem' }}>{info.bodyEn}</p>
            <p style={{ color: '#334155', fontStyle: 'normal' }}>{info.bodyTa}</p>
          </div>

          {/* Citizen & Sanction Details Box */}
          <div
            style={{
              border: '1px dashed #cbd5e1',
              background: '#ffffff',
              padding: '1rem 1.25rem',
              borderRadius: '6px',
              marginBottom: '2rem',
              fontSize: '0.88rem',
            }}
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
              <div>
                <span style={{ color: '#64748b' }}>Applicant Name:</span>
                <div style={{ fontWeight: 700, color: '#0f3460', fontSize: '1rem' }}>{user.full_name}</div>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Aadhaar / ID Ref:</span>
                <div style={{ fontWeight: 600 }}>XXXX-XXXX-4819 (Masked DPDP)</div>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Permanent State:</span>
                <div style={{ fontWeight: 600 }}>Tamil Nadu, India</div>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Sanction Parameters:</span>
                <div style={{ fontWeight: 700, color: '#059669' }}>{info.sanctionDetails}</div>
              </div>
            </div>
          </div>

          {/* Footer Seals & Digital Signature */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', paddingTop: '1rem', borderTop: '1px solid #e2e8f0' }}>
            {/* QR Code Simulation */}
            <div style={{ textAlign: 'center' }}>
              <div
                style={{
                  width: '84px',
                  height: '84px',
                  border: '2px solid #0f3460',
                  padding: '4px',
                  background: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.65rem',
                  color: '#0f3460',
                  fontWeight: 800,
                  flexDirection: 'column',
                  gap: '4px',
                }}
              >
                <div style={{ width: '100%', height: '56px', background: 'repeating-linear-gradient(45deg, #0f3460 0, #0f3460 3px, #ffffff 3px, #ffffff 6px)' }} />
                <span>TN-VERIFY</span>
              </div>
              <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.3rem' }}>Scan to Authenticate</div>
            </div>

            {/* Verification Center */}
            <div style={{ textAlign: 'center' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#059669', fontWeight: 700, fontSize: '0.85rem', marginBottom: '0.25rem' }}>
                <ShieldCheck size={18} />
                <span>Digitally Signed & Validated</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Tamil Nadu State Resident Data Hub (SRDH)</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>No Physical Signature Required (IT Act 2000)</div>
            </div>

            {/* Official Seal */}
            <div style={{ textAlign: 'center' }}>
              <div
                style={{
                  width: '90px',
                  height: '90px',
                  borderRadius: '50%',
                  border: '2px solid #b45309',
                  color: '#b45309',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.62rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  padding: '4px',
                  lineHeight: '1.2',
                }}
              >
                <span>★ GOVT OF TN ★</span>
                <span style={{ fontSize: '0.75rem', color: '#0f3460' }}>REVENUE</span>
                <span>ZONAL TAHSILDAR</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.75rem' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handlePrint}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '0.65rem 1.25rem' }}
          >
            <Printer size={16} />
            <span>{language === 'ta' ? 'அச்சிடுக (Print)' : 'Print Certificate'}</span>
          </button>

          <button
            type="button"
            className="btn btn-primary"
            onClick={handlePrint}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '0.65rem 1.5rem', background: '#059669' }}
          >
            <Download size={16} />
            <span>{language === 'ta' ? 'சான்றிதழைப் பதிவிறக்குக (Download PDF)' : 'Download Official Certificate'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

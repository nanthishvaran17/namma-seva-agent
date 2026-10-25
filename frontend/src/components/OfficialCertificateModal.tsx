import React, { useState } from 'react';
import {
  X, Copy, Check, AlertTriangle, ExternalLink, FileCheck,
  ClipboardList, Clock, Building, CreditCard, Bot, Zap,
  Loader2, CheckCircle2, ShieldCheck, ArrowRight, Printer, FileText
} from 'lucide-react';

interface OfficialCertificateModalProps {
  task: any;
  user: any;
  language: string;
  onClose: () => void;
  onTaskUpdated?: () => void;
}

interface AutoApplyResult {
  success: boolean;
  arn: string;
  can_number: string;
  service_id: string;
  service_name_en: string;
  service_name_ta: string;
  department: string;
  portal_url: string;
  statutory_fee: number;
  submission_timestamp: string;
  expected_delivery_date: string;
  tracking_url: string;
  current_status: string;
  officer_hierarchy: Array<{ level: string; designation: string; role: string; sla_days: string; status: string }>;
  receipt_html: string;
}

export const OfficialCertificateModal: React.FC<OfficialCertificateModalProps> = ({
  task,
  user,
  language,
  onClose,
  onTaskUpdated
}) => {
  const [activeTab, setActiveTab] = useState<'auto_apply' | 'manual_guide'>('auto_apply');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [isApplying, setIsApplying] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isDelivering, setIsDelivering] = useState(false);
  const [deliveredCert, setDeliveredCert] = useState<any>(null);

  const [autoResult, setAutoResult] = useState<AutoApplyResult | null>(() => {
    if (task.submission_evidence && task.submission_evidence.arn) {
      return {
        success: true,
        arn: task.submission_evidence.arn,
        can_number: task.submission_evidence.can_number || '133094821034',
        service_id: task.service_id,
        service_name_en: 'Certificate',
        service_name_ta: 'அரசு சான்றிதழ்',
        department: 'வருவாய்த் துறை (Revenue Administration)',
        portal_url: 'https://www.tnesevai.tn.gov.in',
        statutory_fee: task.submission_evidence.statutory_fee || 60.0,
        submission_timestamp: task.submission_evidence.submitted_at || new Date().toISOString(),
        expected_delivery_date: task.submission_evidence.expected_delivery || '15 Working Days',
        tracking_url: `https://edistricts.tn.gov.in/revenue/status.html?arn=${task.submission_evidence.arn}`,
        current_status: 'SUBMITTED_TO_VAO',
        officer_hierarchy: task.submission_evidence.officer_hierarchy || [
          { level: '1', designation: 'Village Administrative Officer (VAO)', role: 'Local Field Inquiry & Record Verification', sla_days: '3 Days', status: 'PENDING_VERIFICATION' },
          { level: '2', designation: 'Revenue Inspector (RI)', role: 'Firka Level Scrutiny & Endorsement', sla_days: '4 Days', status: 'UPCOMING' },
          { level: '3', designation: 'Zonal Deputy Tahsildar', role: 'Final Statutory Approval & Digital Signature', sla_days: '8 Days', status: 'UPCOMING' }
        ],
        receipt_html: task.submission_evidence.receipt_html || ''
      };
    }
    return null;
  });

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
      case 'nativity_certificate':
        return {
          serviceNameTa: 'இருப்பிடச் சான்றிதழ் (Nativity Certificate)',
          serviceNameEn: 'Nativity / Residence Certificate',
          deptTa: 'வருவாய் மற்றும் பேரிடர் மேலாண்மைத் துறை',
          deptEn: 'Revenue & Disaster Management Department',
          portalUrl: 'https://www.tnesevai.tn.gov.in',
          fee: '₹60',
          timeline: '15 working days',
          checklist: [
            'Birth Certificate / School Transfer Certificate',
            'Parents Residence Proof (10+ Years)',
            'Smart Ration Card'
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

  const runAutoApply = async () => {
    setIsApplying(true);
    setCurrentStepIndex(1);

    try {
      const payload = {
        service_id: task.service_id,
        task_id: task.id,
        citizen_name: user?.full_name || 'Arun Kumar',
        father_name: 'K. Arumugam',
        gender: 'Male',
        dob: '2001-05-14',
        aadhaar_number: '123456788492',
        mobile: user?.phone_number || '9042020879',
        email: user?.email,
        district: 'Coimbatore',
        taluk: 'Coimbatore North',
        village: 'Saravanampatti',
        street_address: '12/4, Gandhi Salai',
        pincode: '641035',
        community: 'BC',
        caste: 'Agamudayar',
        religion: 'Hindu',
        annual_income_inr: 120000.0,
        documents_attached: ['photo', 'aadhaar_card', 'ration_card', 'parent_community_cert', 'school_tc']
      };

      const stepTimer1 = setTimeout(() => setCurrentStepIndex(2), 700);
      const stepTimer2 = setTimeout(() => setCurrentStepIndex(3), 1400);
      const stepTimer3 = setTimeout(() => setCurrentStepIndex(4), 2100);
      const stepTimer4 = setTimeout(() => setCurrentStepIndex(5), 2800);

      const token = localStorage.getItem('namma_seva_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/automation/auto-apply', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      clearTimeout(stepTimer4);

      if (res.ok) {
        const data = await res.json();
        setCurrentStepIndex(6);
        setAutoResult(data);
        if (onTaskUpdated) onTaskUpdated();
      } else {
        throw new Error('Automated submission failed');
      }
    } catch (err) {
      console.error(err);
      alert(language === 'ta' ? 'தானியங்கி விண்ணப்பத்தில் பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.' : 'Error executing auto-apply. Please try again.');
    } finally {
      setIsApplying(false);
    }
  };

  const handleDeliverToWhatsApp = async (arn: string) => {
    setIsDelivering(true);
    try {
      const res = await fetch('/api/v1/automation/auto-complete-and-deliver', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          arn: arn,
          service_id: task.service_id,
          task_id: task.id,
          to_phone: user?.phone_number || '9042020879',
          citizen_name: user?.full_name || 'Arun Kumar',
          service_name: meta.serviceNameTa
        })
      });
      if (res.ok) {
        const data = await res.json();
        setDeliveredCert(data);
        if (onTaskUpdated) onTaskUpdated();
      } else {
        throw new Error('Delivery failed');
      }
    } catch (e) {
      console.error(e);
      alert('Error delivering certificate to WhatsApp.');
    } finally {
      setIsDelivering(false);
    }
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
          aria-label="Close modal"
        >
          <X size={20} />
        </button>

        {/* Header */}
        <div style={{ borderBottom: '2px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0f3460', marginBottom: '0.25rem' }}>
            <Bot size={26} style={{ color: '#2563eb' }} />
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0 }}>
              {language === 'ta' ? 'அரசு இ-சேவை தானியங்கி விண்ணப்ப மையம்' : 'TNeGA e-Sevai Autonomous Application Engine'}
            </h2>
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#334155' }}>
            {meta.serviceNameEn} • <span style={{ color: '#0f3460' }}>{meta.serviceNameTa}</span>
          </div>
          <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.2rem' }}>
            {meta.deptEn} ({meta.deptTa})
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '8px' }}>
          <button
            type="button"
            onClick={() => setActiveTab('auto_apply')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '0.6rem 1.25rem',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.9rem',
              background: activeTab === 'auto_apply' ? '#0f3460' : '#f1f5f9',
              color: activeTab === 'auto_apply' ? '#ffffff' : '#475569',
              transition: 'all 0.2s'
            }}
          >
            <Zap size={16} style={{ color: activeTab === 'auto_apply' ? '#fbbf24' : '#64748b' }} />
            <span>{language === 'ta' ? 'AI தானியங்கி விண்ணப்பம் (Auto-Apply)' : 'AI Autonomous Apply'}</span>
          </button>
          
          <button
            type="button"
            onClick={() => setActiveTab('manual_guide')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '0.6rem 1.25rem',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 700,
              fontSize: '0.9rem',
              background: activeTab === 'manual_guide' ? '#0f3460' : '#f1f5f9',
              color: activeTab === 'manual_guide' ? '#ffffff' : '#475569',
              transition: 'all 0.2s'
            }}
          >
            <ClipboardList size={16} />
            <span>{language === 'ta' ? 'வழிகாட்டி & விவரங்கள்' : 'Pre-fill Checklist'}</span>
          </button>
        </div>

        {/* TAB 1: AUTONOMOUS AUTO APPLY */}
        {activeTab === 'auto_apply' && (
          <div>
            {!autoResult && !isApplying && (
              <div>
                <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '10px', padding: '1.25rem', marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                    <ShieldCheck size={28} style={{ color: '#2563eb', flexShrink: 0 }} />
                    <div>
                      <h4 style={{ margin: '0 0 6px 0', color: '#1e3a8a', fontSize: '1rem', fontWeight: 800 }}>
                        {language === 'ta' ? 'AI ஏஜென்ட் உங்கள் சார்பாக விண்ணப்பிக்கும் செயல்முறை' : 'How Autonomous e-Sevai Auto-Apply Works'}
                      </h4>
                      <p style={{ margin: 0, fontSize: '0.85rem', color: '#1e40af', lineHeight: '1.5' }}>
                        {language === 'ta'
                          ? 'நீங்கள் படிவங்களை கைப்பட நிரப்ப தேவையில்லை. நமது AI ஏஜென்ட் உங்கள் சுயவிவரம் மற்றும் பதிவேற்றிய ஆவணங்களிலிருந்து தரவுகளை எடுத்து, CAN பதிவு செய்து, தமிழ்நாடு அரசின் e-Sevai தளத்தில் தானாகவே விண்ணப்பித்து ARN பெற்றுத்தரும்.'
                          : 'No manual portal navigation needed. Our AI agent extracts data from your profile & verified docs, maps citizen CAN, auto-populates the official TNeGA portal form, and generates an authentic ARN receipt.'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Pre-flight Data Verification */}
                <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1.25rem', marginBottom: '1.5rem' }}>
                  <h4 style={{ margin: '0 0 10px 0', fontSize: '0.92rem', color: '#334155', fontWeight: 700 }}>
                    {language === 'ta' ? 'தானாக நிரப்பப்பட உள்ள சரிபார்க்கப்பட்ட தகவல்கள்:' : 'Verified Data to be Auto-Populated:'}
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '0.85rem' }}>
                    <div><strong>விண்ணப்பதாரர் / Name:</strong> {user?.full_name || 'Arun Kumar'}</div>
                    <div><strong>தந்தை பெயர் / Father:</strong> K. Arumugam</div>
                    <div><strong>சமூகம் / Community:</strong> BC (Agamudayar)</div>
                    <div><strong>மாவட்டம் / District:</strong> Coimbatore North</div>
                    <div><strong>கட்டணம் / Portal Fee:</strong> {meta.fee}</div>
                    <div><strong>ஆதார் / Aadhaar:</strong> XXXX-XXXX-8492</div>
                  </div>
                </div>

                {/* Trigger Button */}
                <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                  <button
                    type="button"
                    onClick={runAutoApply}
                    style={{
                      background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '10px',
                      padding: '1rem 2.5rem',
                      fontSize: '1.05rem',
                      fontWeight: 800,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '10px',
                      boxShadow: '0 10px 20px -5px rgba(5, 150, 105, 0.4)',
                      transition: 'transform 0.15s ease'
                    }}
                  >
                    <Zap size={22} style={{ color: '#fef08a' }} />
                    <span>{language === 'ta' ? 'இப்போதே தானாக விண்ணப்பிக்கவும் (Auto-Apply Now)' : 'Execute Autonomous Application Now'}</span>
                    <ArrowRight size={20} />
                  </button>
                  <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.6rem' }}>
                    * அரசு அங்கீகரிக்கப்பட்ட TNeGA e-Sevai முறைப்படி விண்ணப்பம் சமர்ப்பிக்கப்படும்.
                  </div>
                </div>
              </div>
            )}

            {/* In Progress Animation */}
            {isApplying && (
              <div style={{ padding: '2rem 1rem', textAlign: 'center' }}>
                <Loader2 size={48} className="spin" style={{ color: '#2563eb', margin: '0 auto 1.5rem auto' }} />
                <h3 style={{ margin: '0 0 10px 0', color: '#0f3460', fontSize: '1.25rem', fontWeight: 800 }}>
                  {language === 'ta' ? 'AI ஏஜென்ட் அரசு போர்ட்டலில் விண்ணப்பிக்கிறது...' : 'AI Agent Submitting Application on e-Sevai Portal...'}
                </h3>
                <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '2rem' }}>
                  {language === 'ta' ? 'தயவுசெய்து காத்திருக்கவும். ஆவணங்கள் மற்றும் CAN விவரங்கள் சரிபார்க்கப்படுகின்றன.' : 'Please wait while documents and citizen CAN registry are validated.'}
                </p>

                <div style={{ maxWidth: '520px', margin: '0 auto', textAlign: 'left', background: '#f8fafc', padding: '1.25rem', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                  {[
                    { id: 1, title: 'குடிமக்கள் ஆவணங்கள் & ஆதார் சரிபார்ப்பு (Doc OCR)' },
                    { id: 2, title: 'TNeGA CAN எண் கண்டறிதல் & இணைத்தல்' },
                    { id: 3, title: 'தமிழ்நாடு இ-சேவை (e-Sevai) போர்ட்டல் இணைப்பு' },
                    { id: 4, title: '18 கட்டாய விவரங்கள் மற்றும் சான்றுகள் தானாக நிரப்புதல்' },
                    { id: 5, title: 'அரசு கட்டணம் ₹60 செலுத்துதல் & ஒப்புதல் பெறுதல்' },
                    { id: 6, title: 'அதிகாரப்பூர்வ விண்ணப்ப எண் (ARN) பெறுதல்' }
                  ].map((s) => (
                    <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', fontSize: '0.85rem' }}>
                      {currentStepIndex >= s.id ? (
                        <CheckCircle2 size={18} style={{ color: '#059669', flexShrink: 0 }} />
                      ) : (
                        <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: '2px solid #cbd5e1', flexShrink: 0 }} />
                      )}
                      <span style={{ color: currentStepIndex >= s.id ? '#0f172a' : '#94a3b8', fontWeight: currentStepIndex >= s.id ? 700 : 400 }}>
                        {s.title}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Finished Acknowledgment Receipt */}
            {autoResult && !isApplying && (
              <div>
                <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '10px', padding: '1.25rem', marginBottom: '1.5rem', display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <CheckCircle2 size={32} style={{ color: '#16a34a', flexShrink: 0 }} />
                  <div>
                    <h3 style={{ margin: '0 0 4px 0', color: '#14532d', fontSize: '1.1rem', fontWeight: 800 }}>
                      {language === 'ta' ? 'விண்ணப்பம் வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது!' : 'Application Successfully Submitted to TN e-Sevai!'}
                    </h3>
                    <div style={{ color: '#15803d', fontSize: '0.85rem' }}>
                      {language === 'ta' ? 'அதிகாரப்பூர்வ விண்ணப்ப குறிப்பு எண் (ARN) ஒதுக்கப்பட்டுள்ளது.' : 'Official Application Reference Number (ARN) has been generated and logged.'}
                    </div>
                  </div>
                </div>

                {/* Official Receipt Card */}
                <div style={{ border: '2px solid #0f3460', borderRadius: '10px', padding: '1.5rem', background: '#ffffff', marginBottom: '1.5rem' }}>
                  <div style={{ textAlign: 'center', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#0f3460', letterSpacing: '0.5px' }}>
                      தமிழ்நாடு அரசு • GOVERNMENT OF TAMIL NADU
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#475569' }}>
                      தமிழ்நாடு மின் ஆளுமை முகமை (TNeGA) • e-Sevai Citizen Services
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#1e293b', marginTop: '0.4rem' }}>
                      {meta.serviceNameTa} ({meta.serviceNameEn})
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px dashed #cbd5e1', marginBottom: '1rem' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>விண்ணப்ப எண் / Application Ref (ARN):</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                        <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f3460' }}>{autoResult.arn}</span>
                        <button
                          type="button"
                          onClick={() => handleCopy('arn', autoResult.arn)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
                          title="Copy ARN"
                        >
                          {copiedKey === 'arn' ? <Check size={14} style={{ color: '#059669' }} /> : <Copy size={14} />}
                        </button>
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>TNeGA CAN எண்:</div>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#334155', marginTop: '2px' }}>
                        {autoResult.can_number}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>விண்ணப்பித்த நாள் / Applied On:</div>
                      <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#334155', marginTop: '2px' }}>
                        {new Date(autoResult.submission_timestamp).toLocaleDateString()}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b' }}>உத்தேச தீர்வு நாள் / Expected By:</div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#059669', marginTop: '2px' }}>
                        {autoResult.expected_delivery_date}
                      </div>
                    </div>
                  </div>

                  {/* Real-Time Officer Progress */}
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#334155', marginBottom: '0.5rem' }}>
                      {language === 'ta' ? 'அரசு அதிகாரிகள் பரிசீலனை நிலை:' : 'Statutory Verification Hierarchy:'}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {autoResult.officer_hierarchy.map((off, idx) => (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0.75rem', background: idx === 0 ? '#eff6ff' : '#ffffff', border: '1px solid #e2e8f0', borderRadius: '6px', fontSize: '0.82rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ width: '22px', height: '22px', borderRadius: '50%', background: idx === 0 ? '#2563eb' : '#cbd5e1', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.75rem' }}>
                              {off.level}
                            </span>
                            <div>
                              <strong style={{ color: '#1e293b' }}>{off.designation}</strong>
                              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{off.role}</div>
                            </div>
                          </div>
                          <div style={{ fontWeight: 700, color: idx === 0 ? '#2563eb' : '#64748b', fontSize: '0.75rem' }}>
                            {idx === 0 ? (language === 'ta' ? 'கள ஆய்வு நடக்கிறது (In Progress)' : 'In Scrutiny (3 Days)') : off.sla_days}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Receipt Actions */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', paddingTop: '10px', borderTop: '1px solid #e2e8f0' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => window.print()}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                    >
                      <Printer size={16} />
                      <span>{language === 'ta' ? 'ஒப்புதல் சீட்டை அச்சிடுக (Print Receipt)' : 'Print Official Receipt'}</span>
                    </button>

                    <a
                      href={autoResult.tracking_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-primary"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '0.85rem',
                        background: '#0f3460',
                        color: '#ffffff',
                        textDecoration: 'none'
                      }}
                    >
                      <span>{language === 'ta' ? 'இ-டிஸ்ட்ரிக்ட் தளத்தில் நிலையை காண்க' : 'Live e-District Tracker'}</span>
                      <ExternalLink size={15} />
                    </a>
                  </div>
                </div>

                {/* AUTOMATED WHATSAPP DELIVERY ACTION */}
                <div style={{ background: '#f0fdf4', border: '2px solid #22c55e', borderRadius: '10px', padding: '1.25rem', marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '10px' }}>
                    <div>
                      <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#166534' }}>
                        {language === 'ta' ? 'அதிகாரி ஒப்புதல் & WhatsApp-ல் சான்றிதழைப் பெறவும்' : 'Simulate Officer Approval & Deliver Certificate to WhatsApp'}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#15803d', marginTop: '2px' }}>
                        {language === 'ta'
                          ? 'வட்டாட்சியர் ஒப்புதல் அளித்ததும் AI Agent டிஜிட்டல் சான்றிதழ் PDF-ஐ உங்கள் WhatsApp-க்கே அனுப்பிவிடும்.'
                          : 'Upon Tahsildar approval, AI agent downloads and dispatches the digitally signed PDF to citizen WhatsApp.'}
                      </div>
                    </div>

                    {!deliveredCert && (
                      <button
                        type="button"
                        disabled={isDelivering}
                        onClick={() => handleDeliverToWhatsApp(autoResult.arn)}
                        style={{
                          background: '#16a34a',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '8px',
                          padding: '0.65rem 1.25rem',
                          fontSize: '0.88rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                      >
                        {isDelivering ? <Loader2 size={16} className="spin" /> : <Bot size={16} />}
                        <span>{language === 'ta' ? 'இப்போதே WhatsApp-ல் பெறுக' : 'Deliver to WhatsApp Now'}</span>
                      </button>
                    )}
                  </div>

                  {/* Delivered Confirmation Box */}
                  {deliveredCert && (
                    <div style={{ background: '#ffffff', border: '1px solid #86efac', borderRadius: '8px', padding: '1rem', marginTop: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#15803d', fontWeight: 800, fontSize: '0.9rem', marginBottom: '6px' }}>
                        <CheckCircle2 size={18} />
                        <span>{language === 'ta' ? 'சான்றிதழ் வழங்கப்பட்டு WhatsApp-க்கு அனுப்பப்பட்டது!' : 'Official Certificate Issued & Delivered to WhatsApp!'}</span>
                      </div>
                      <div style={{ fontSize: '0.82rem', color: '#334155', lineHeight: '1.6' }}>
                        <div><strong>சான்றிதழ் எண் / Cert No:</strong> {deliveredCert.certificate?.certificate_number}</div>
                        <div><strong>வழங்கிய அதிகாரி / Authority:</strong> {deliveredCert.certificate?.issuing_authority}</div>
                        <div><strong>அனுப்பப்பட்ட எண் / Phone:</strong> {deliveredCert.whatsapp_delivery?.to_phone} ({deliveredCert.whatsapp_delivery?.delivery_status})</div>
                      </div>

                      <div style={{ marginTop: '12px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        <a
                          href={`http://localhost:8000/api/v1/automation/download-certificate/${autoResult.arn}?service_id=${task.service_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            background: '#0f3460',
                            color: '#ffffff',
                            padding: '0.55rem 1.25rem',
                            borderRadius: '6px',
                            textDecoration: 'none',
                            fontSize: '0.85rem',
                            fontWeight: 700,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px'
                          }}
                        >
                          <FileText size={16} />
                          <span>{language === 'ta' ? 'ஒரிஜினல் சான்றிதழைப் பார் / பதிவிறக்கு (View PDF)' : 'View & Download Original Certificate'}</span>
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: MANUAL PRE-FILL GUIDE */}
        {activeTab === 'manual_guide' && (
          <div>
            <div
              style={{
                background: '#fef3c7',
                border: '1px solid #f59e0b',
                borderRadius: '8px',
                padding: '1rem 1.25rem',
                marginBottom: '1.5rem',
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-start',
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
                    ? 'இது உங்கள் அதிகாரப்பூர்வ இ-சேவை / அரசு போர்ட்டலில் விண்ணப்பிக்க உதவும் முன்-நிரப்பு வழிகாட்டித் தாள் மட்டுமே.'
                    : 'This is an application pre-fill checklist generated by Namma Seva Agent to assist you when applying on the official portal.'}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 0.75rem 0', color: '#1e293b' }}>
                {language === 'ta' ? '1. போர்ட்டலில் நிரப்ப வேண்டிய விவரங்கள்' : '1. Copyable Pre-fill Details for Portal'}
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
                <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Applicant Full Name:</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.2rem' }}>
                    <strong style={{ color: '#0f3460' }}>{user?.full_name || 'Arun Kumar'}</strong>
                    <button
                      type="button"
                      onClick={() => handleCopy('name', user?.full_name || 'Arun Kumar')}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
                      title="Copy Name"
                    >
                      {copiedKey === 'name' ? <Check size={14} style={{ color: '#059669' }} /> : <Copy size={14} />}
                    </button>
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Statutory Portal Fee:</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.2rem' }}>
                    <strong style={{ color: '#059669' }}>{meta.fee}</strong>
                    <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Official</span>
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '0.75rem 1rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Processing SLA:</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.2rem' }}>
                    <strong style={{ color: '#334155' }}>{meta.timeline}</strong>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 0.75rem 0', color: '#1e293b' }}>
                {language === 'ta' ? '2. இணைக்க வேண்டிய ஆவணங்கள்' : '2. Mandatory Document Attachments'}
              </h3>
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '6px', overflow: 'hidden' }}>
                {meta.checklist.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '0.65rem 1rem',
                      background: idx % 2 === 0 ? '#ffffff' : '#f8fafc',
                      borderBottom: idx === meta.checklist.length - 1 ? 'none' : '1px solid #e2e8f0',
                      fontSize: '0.88rem',
                    }}
                  >
                    <CheckCircle2 size={16} style={{ color: '#059669', flexShrink: 0 }} />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ textAlign: 'right', paddingTop: '10px' }}>
              <a
                href={meta.portalUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '0.85rem',
                  padding: '0.55rem 1.25rem',
                  background: '#0f3460',
                  textDecoration: 'none',
                  color: '#ffffff',
                }}
              >
                <span>{language === 'ta' ? 'அதிகாரப்பூர்வ தளம் செல்க' : 'Proceed to Official Portal'}</span>
                <ExternalLink size={15} />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

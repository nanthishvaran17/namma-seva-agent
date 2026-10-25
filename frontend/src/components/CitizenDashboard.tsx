import React, { useState, useEffect } from 'react';
import {
  CheckSquare,
  ArrowRight,
  Download,
  Trash2,
  Clock,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
  Award,
  Sparkles,
  Eye,
  RefreshCw
} from 'lucide-react';
import { ApiClient } from '../services/api';
import type { UserTask, UserProfile } from '../types';
import { OfficialCertificateModal } from './OfficialCertificateModal';

interface CitizenDashboardProps {
  language: string;
  user: UserProfile;
  onSelectService: () => void;
}

interface RequiredDocDef {
  code: string;
  nameTa: string;
  nameEn: string;
  mandatory: boolean;
}

const SERVICE_DOC_MAP: Record<string, RequiredDocDef[]> = {
  community_certificate: [
    { code: 'photo', nameTa: 'பாஸ்போர்ட் அளவு புகைப்படம்', nameEn: 'Applicant Passport Photo', mandatory: true },
    { code: 'address_proof', nameTa: 'முகவரிச் சான்று (ஸ்மார்ட் கார்டு / ஆதார்)', nameEn: 'Proof of Address (Ration/Aadhaar)', mandatory: true },
    { code: 'community_proof_family', nameTa: 'தந்தை/தாய் சாதிச் சான்றிதழ்', nameEn: 'Parent Community Certificate', mandatory: true },
  ],
  income_certificate: [
    { code: 'ration_card', nameTa: 'ஸ்மார்ட் குடும்ப அட்டை', nameEn: 'Smart Ration Card', mandatory: true },
    { code: 'income_proof', nameTa: 'சம்பளச் சான்று அல்லது உறுதிமொழி', nameEn: 'Salary Certificate / Self Declaration', mandatory: true },
    { code: 'aadhaar', nameTa: 'ஆதார் அட்டை', nameEn: 'Aadhaar Card', mandatory: true },
  ],
  nativity_certificate: [
    { code: 'birth_cert', nameTa: 'பிறப்புச் சான்றிதழ்', nameEn: 'Birth Certificate', mandatory: true },
    { code: 'residence_proof', nameTa: '5 வருட குடியிருப்பு ஆதாரம்', nameEn: '5-Year Residence Proof', mandatory: true },
  ],
  first_graduate_certificate: [
    { code: 'ration_card', nameTa: 'குடும்ப அட்டை (Ration Card)', nameEn: 'Smart Ration Card', mandatory: true },
    { code: 'transfer_cert', nameTa: 'பள்ளி மாற்றுச் சான்றிதழ் (TC)', nameEn: 'Applicant School Transfer Certificate', mandatory: true },
    { code: 'parent_affidavit', nameTa: 'பெற்றோர் உறுதிமொழிப் பத்திரம்', nameEn: 'Family Member Declaration Affidavit', mandatory: true },
  ],
  post_matric_scholarship: [
    { code: 'community_cert', nameTa: 'சாதிச் சான்றிதழ் (Community Cert)', nameEn: 'Community Certificate', mandatory: true },
    { code: 'income_cert', nameTa: 'வருமானச் சான்றிதழ் (வருமானம் < ₹2.5L)', nameEn: 'Income Certificate (< ₹2.5L/yr)', mandatory: true },
    { code: 'college_bonafide', nameTa: 'கல்லூரி சேர்க்கை சான்றிதழ் (Bonafide)', nameEn: 'College Admission Bonafide', mandatory: true },
    { code: 'bank_passbook', nameTa: 'ஆதார் இணைக்கப்பட்ட வங்கிக் கணக்குப் புத்தகம்', nameEn: 'Aadhaar-Seeded Bank Passbook', mandatory: true },
  ],
};

export const CitizenDashboard: React.FC<CitizenDashboardProps> = ({
  language,
  user,
  onSelectService,
}) => {
  const [tasks, setTasks] = useState<UserTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Modal for Viewing Official Issued Certificate
  const [activeCertTask, setActiveCertTask] = useState<UserTask | null>(null);

  // Track uploaded documents per task in state
  const [uploadedDocs, setUploadedDocs] = useState<Record<string, Record<string, any>>>({});
  const [scanningDoc, setScanningDoc] = useState<string | null>(null);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const data = await ApiClient.getTasks();
      setTasks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const exportJson = await ApiClient.exportData();
      const blob = new Blob([JSON.stringify(exportJson, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `namma_seva_citizen_data_${user.id.slice(0, 8)}.json`;
      a.click();
      setMessage(language === 'ta' ? 'உங்கள் தகவல்கள் வெற்றிகரமாக பதிவிறக்கம் செய்யப்பட்டன (சட்ட ஆலோசனைக்கு உட்பட்டது).' : 'Your personal data archive was exported successfully (pending legal review).');
    } catch (err: any) {
      setMessage(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteData = async () => {
    if (window.confirm('Are you absolutely sure you want to permanently erase your account, all application tasks, and document metadata? This action is irreversible (pending legal review).')) {
      try {
        await ApiClient.deleteData();
        localStorage.removeItem('namma_seva_token');
        window.location.reload();
      } catch (err: any) {
        setMessage(`Deletion failed: ${err.message}`);
      }
    }
  };

  const handleUpdateStatus = async (taskId: string, newStatus: string) => {
    try {
      await ApiClient.updateTaskStatus(taskId, newStatus, 'Citizen progress automation');
      await loadTasks();
      setMessage(
        language === 'ta'
          ? `விண்ணப்ப நிலை வெற்றிகரமாக மாற்றப்பட்டது: ${newStatus}`
          : `Task status progressed successfully to: ${newStatus}`
      );
    } catch (err: any) {
      alert(`Cannot advance state: ${err.message}`);
    }
  };

  // Demo Mode: Fast-fill sample checklist to preview the application pre-fill sheet
  const handleAutoFastTrack = async (task: UserTask) => {
    try {
      setScanningDoc(`${task.id}-all`);
      await new Promise((res) => setTimeout(res, 600));

      // 1. Advance to READY_FOR_USER_REVIEW
      await ApiClient.updateTaskStatus(task.id, 'READY_FOR_USER_REVIEW', 'DEMO: Pre-filled sample document checklist');
      // 2. Advance to READY_TO_SUBMIT
      await ApiClient.updateTaskStatus(task.id, 'READY_TO_SUBMIT', 'DEMO: Pre-fill details verified');
      // 3. Mark completed for pre-fill generation
      await ApiClient.updateTaskStatus(task.id, 'COMPLETED', 'DEMO: Ready for portal submission');

      await loadTasks();
      setActiveCertTask({ ...task, status: 'COMPLETED' });
      setMessage(
        language === 'ta'
          ? 'விண்ணப்ப முன்-நிரப்பு விவரத் தாள் மாதிரி முறையில் தயார் செய்யப்பட்டுள்ளது (DEMO).'
          : 'Demo Mode: Sample application checklist and pre-fill sheet generated.'
      );
    } catch (err: any) {
      alert(`Demo workflow error: ${err.message}`);
    } finally {
      setScanningDoc(null);
    }
  };

  const handleSimulateUpload = (taskId: string, docCode: string) => {
    setScanningDoc(`${taskId}-${docCode}`);
    setTimeout(() => {
      setUploadedDocs((prev) => ({
        ...prev,
        [taskId]: {
          ...(prev[taskId] || {}),
          [docCode]: {
            fileName: `${docCode}_verified.pdf`,
            extractedName: user.full_name,
            idNumber: 'XXXX-XXXX-4819',
            verifiedAt: new Date().toLocaleTimeString(),
            confidence: '99.8%'
          }
        }
      }));
      setScanningDoc(null);
    }, 700);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span style={{ background: '#d1fae5', color: '#059669', padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Award size={14} />
            <span>COMPLETED / சான்றிதழ் தயார்</span>
          </span>
        );
      case 'READY_TO_SUBMIT':
        return (
          <span style={{ background: '#fef3c7', color: '#b45309', padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle2 size={14} />
            <span>READY TO SUBMIT / சமர்ப்பிக்க தயார்</span>
          </span>
        );
      case 'READY_FOR_USER_REVIEW':
        return (
          <span style={{ background: '#e0e7ff', color: '#4338ca', padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Clock size={14} />
            <span>READY FOR REVIEW / சரிபார்ப்புக்கு தயார்</span>
          </span>
        );
      case 'COLLECTING_DOCUMENTS':
        return (
          <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
            <Upload size={14} />
            <span>COLLECTING DOCS / ஆவணங்கள் தேவை</span>
          </span>
        );
      default:
        return (
          <span style={{ background: '#f1f5f9', color: '#475569', padding: '0.35rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 800 }}>
            {status}
          </span>
        );
    }
  };

  const getProgressPercentage = (status: string) => {
    switch (status) {
      case 'DRAFT': return 15;
      case 'COLLECTING_DOCUMENTS': return 35;
      case 'READY_FOR_USER_REVIEW': return 65;
      case 'READY_TO_SUBMIT': return 85;
      case 'SUBMITTED': return 95;
      case 'COMPLETED': return 100;
      default: return 30;
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '1rem 0' }}>
      {/* Welcome Banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
          border: '1px solid #e2e8f0',
          borderRadius: '1rem',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 4px 15px rgba(15, 52, 96, 0.05)',
          flexWrap: 'wrap',
          gap: '1.25rem',
        }}
      >
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: '#e0f2fe', color: '#0369a1', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            <ShieldCheck size={14} />
            <span>DPDP 2023 Verified Citizen Account</span>
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f3460', marginBottom: '0.35rem' }}>
            {language === 'ta' ? `வணக்கம், ${user.full_name}!` : `Welcome back, ${user.full_name}!`}
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.92rem', maxWidth: '650px', lineHeight: '1.5' }}>
            {language === 'ta'
              ? 'உங்கள் அரசு சேவை விண்ணப்பங்களை AI மூலம் முழுமையாக தானியங்கி முறையில் சரிபார்த்து, அதிகாரப்பூர்வ சான்றிதழ்களை உடனடியாகப் பெறுங்கள்.'
              : 'Monitor your active civic workflows, upload documents for AI OCR auto-verification, and download officially verified certificates.'}
          </p>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={onSelectService}
          style={{ padding: '0.75rem 1.5rem', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <span>{language === 'ta' ? 'புதிய சேவை தொடங்குக' : 'Start New Application'}</span>
          <ArrowRight size={16} />
        </button>
      </div>

      {message && (
        <div
          style={{
            padding: '1rem 1.25rem',
            background: '#ecfdf5',
            color: '#065f46',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            fontSize: '0.92rem',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            border: '1px solid #a7f3d0',
          }}
        >
          <CheckCircle2 size={18} color="#059669" />
          <span style={{ fontWeight: 600 }}>{message}</span>
        </div>
      )}

      {/* Tasks Section */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#0f3460' }}>
              {language === 'ta' ? 'செயலில் உள்ள பணிகள் (Active Application Tasks)' : 'Active Application Tasks'} ({tasks.length})
            </h3>
            <span style={{ fontSize: '0.85rem', color: '#64748b' }}>
              {language === 'ta' ? 'அனைத்து நிலைகளும் AI மற்றும் e-Sevai விதிகளின்படி தானியங்கி முறையில் இயங்குகின்றன.' : 'End-to-end automated workflows grounded in TNeGA citizen charters.'}
            </span>
          </div>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadTasks}
            style={{ padding: '0.45rem 0.9rem', fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} />
            <span>{language === 'ta' ? 'புதுப்பிக்க (Refresh)' : 'Refresh'}</span>
          </button>
        </div>

        {tasks.length === 0 ? (
          <div style={{ textAlign: 'center', background: 'white', padding: '3.5rem 2rem', borderRadius: '1rem', border: '1px dashed #cbd5e1' }}>
            <CheckSquare size={42} color="#94a3b8" style={{ margin: '0 auto 1rem' }} />
            <h4 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#0f3460', marginBottom: '0.5rem' }}>
              {language === 'ta' ? 'தற்போது பணிகள் ஏதுமில்லை' : 'No active application tasks'}
            </h4>
            <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1.5rem' }}>
              {language === 'ta' ? 'சாதி, வருமானம், இருப்பிடம் அல்லது கல்வி உதவித்தொகை விண்ணப்பங்களை இப்போது தொடங்கவும்.' : 'Select a verified service to initiate a guided application.'}
            </p>
            <button type="button" className="btn btn-primary" onClick={onSelectService}>
              <span>{language === 'ta' ? 'சேவை பட்டியலைப் பார்க்கவும்' : 'Browse Services'}</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
            {tasks.map((t) => {
              const reqDocs = SERVICE_DOC_MAP[t.service_id] || [
                { code: 'id_proof', nameTa: 'அடையாளச் சான்று', nameEn: 'Identity Proof', mandatory: true }
              ];
              const taskDocs = uploadedDocs[t.id] || {};
              const progress = getProgressPercentage(t.status);
              const isCompleted = t.status === 'COMPLETED';

              return (
                <div
                  key={t.id}
                  style={{
                    background: 'white',
                    border: isCompleted ? '2px solid #10b981' : '1px solid #e2e8f0',
                    borderRadius: '1rem',
                    padding: '1.75rem',
                    boxShadow: '0 4px 12px rgba(15, 52, 96, 0.06)',
                    position: 'relative',
                  }}
                >
                  {/* Top Bar */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <h4 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0f3460' }}>
                          {t.service_id.replace(/_/g, ' ').toUpperCase()}
                        </h4>
                        {isCompleted && (
                          <span style={{ background: '#d1fae5', color: '#065f46', fontSize: '0.75rem', fontWeight: 800, padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                            OFFICIALLY ISSUED
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>
                        Task ID: <span style={{ fontFamily: 'monospace' }}>{t.id}</span> • Initiated: {new Date(t.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    {getStatusBadge(t.status)}
                  </div>

                  {/* Visual 4-Step Progress Stepper */}
                  <div style={{ marginBottom: '1.5rem', background: '#f8fafc', padding: '1rem 1.25rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 700, color: '#475569', marginBottom: '0.5rem' }}>
                      <span style={{ color: progress >= 25 ? '#0f3460' : '#94a3b8' }}>1. ஆவணங்கள் (Documents)</span>
                      <span style={{ color: progress >= 65 ? '#0f3460' : '#94a3b8' }}>2. ஆய்வு (Review)</span>
                      <span style={{ color: progress >= 85 ? '#0f3460' : '#94a3b8' }}>3. சரிபார்ப்பு (Verified)</span>
                      <span style={{ color: progress === 100 ? '#059669' : '#94a3b8' }}>4. விவரத் தாள் (Pre-fill Sheet)</span>
                    </div>

                    {/* Progress Bar */}
                    <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${progress}%`,
                          height: '100%',
                          background: isCompleted ? '#10b981' : 'linear-gradient(90deg, #0f3460 0%, #ff9900 100%)',
                          borderRadius: '4px',
                          transition: 'width 0.4s ease',
                        }}
                      />
                    </div>
                  </div>

                  {/* Required Documents Interactive Grid */}
                  <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#0f3460', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {language === 'ta' ? 'தேவையான ஆவணங்கள் சரிபார்ப்பு (Document Checklist)' : 'Required Documents & Checklist'}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
                      {reqDocs.map((doc) => {
                        const isUploaded = !!taskDocs[doc.code] || progress >= 65;
                        const isScanning = scanningDoc === `${t.id}-${doc.code}` || scanningDoc === `${t.id}-all`;

                        return (
                          <div
                            key={doc.code}
                            style={{
                              border: isUploaded ? '1px solid #10b981' : '1px dashed #cbd5e1',
                              background: isUploaded ? '#f0fdf4' : '#ffffff',
                              borderRadius: '8px',
                              padding: '0.85rem 1rem',
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              gap: '0.75rem',
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: isUploaded ? '#065f46' : '#1e293b' }}>
                                {language === 'ta' ? doc.nameTa : doc.nameEn}
                              </div>
                              <div style={{ fontSize: '0.75rem', color: isUploaded ? '#059669' : '#64748b', marginTop: '0.15rem' }}>
                                {isUploaded
                                  ? (language === 'ta' ? 'மாதிரி பதிவேற்றம் (DEMO)' : 'DEMO: Verified for preview')
                                  : (language === 'ta' ? 'ஆவணம் தேவை (Mandatory)' : 'Document Required (Mandatory)')}
                              </div>
                            </div>

                            {!isUploaded && !isCompleted && (
                              <button
                                type="button"
                                className="btn btn-secondary"
                                disabled={isScanning}
                                onClick={() => handleSimulateUpload(t.id, doc.code)}
                                style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem', whiteSpace: 'nowrap' }}
                              >
                                {isScanning ? 'சரிபார்க்கிறது...' : 'Demo Upload'}
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Next Action Banner */}
                  <div style={{ background: '#f8fafc', padding: '0.9rem 1.15rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.5rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#0f3460', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
                      {language === 'ta' ? 'அடுத்த கட்ட நடவடிக்கை (Recommended Next Action)' : 'Recommended Next Action'}
                    </div>
                    <div style={{ fontSize: '0.92rem', color: '#1e293b', fontWeight: 600 }}>
                      {isCompleted
                        ? (language === 'ta' ? 'விண்ணப்ப முன்-நிரப்பு விவரத் தாள் தயார். அதிகாரப்பூர்வ அரசு போர்ட்டலில் விண்ணப்பிக்க கீழே உள்ள பொத்தானைப் பயன்படுத்தவும்.' : 'Your application pre-fill checklist is ready. Use the pre-fill sheet below when applying on the official portal.')
                        : (language === 'ta' ? t.next_action_ta : t.next_action_en)}
                    </div>
                  </div>

                  {/* Bottom Action Controls */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
                    {/* Demo Pre-fill Fast Track Button */}
                    {!isCompleted ? (
                      <button
                        type="button"
                        onClick={() => handleAutoFastTrack(t)}
                        disabled={scanningDoc !== null}
                        style={{
                          background: '#f1f5f9',
                          color: '#0f3460',
                          border: '1px solid #cbd5e1',
                          padding: '0.55rem 1.1rem',
                          borderRadius: '6px',
                          fontSize: '0.85rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <Sparkles size={16} color="#d97706" />
                        <span>
                          {scanningDoc
                            ? (language === 'ta' ? 'தயாராகிறது...' : 'Processing...')
                            : (language === 'ta' ? 'மாதிரி விவரத் தாளை நிரப்புக (Demo)' : 'DEMO: Fill Sample Checklist')}
                        </span>
                      </button>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#059669', fontWeight: 700, fontSize: '0.88rem' }}>
                        <ShieldCheck size={18} />
                        <span>{language === 'ta' ? 'விவரத் தாள் தயார் (Ready for Submission)' : 'Pre-fill Sheet Ready'}</span>
                      </div>
                    )}

                    {/* Step-by-Step State Advancement Buttons */}
                    <div style={{ display: 'flex', gap: '0.65rem' }}>
                      {t.status === 'COLLECTING_DOCUMENTS' && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                          onClick={() => handleUpdateStatus(t.id, 'READY_FOR_USER_REVIEW')}
                        >
                          <CheckCircle2 size={15} />
                          <span>{language === 'ta' ? 'ஆவணங்கள் தயார் (Next)' : 'Confirm Documents Ready'}</span>
                        </button>
                      )}

                      {t.status === 'READY_FOR_USER_REVIEW' && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                          onClick={() => handleUpdateStatus(t.id, 'READY_TO_SUBMIT')}
                        >
                          <CheckCircle2 size={15} />
                          <span>{language === 'ta' ? 'விவரங்களை உறுதிசெய் (Confirm Details)' : 'Confirm Verified Details'}</span>
                        </button>
                      )}

                      {t.status === 'READY_TO_SUBMIT' && (
                        <button
                          type="button"
                          className="btn btn-primary"
                          style={{ fontSize: '0.85rem', padding: '0.5rem 1.1rem', background: '#059669' }}
                          onClick={() => handleUpdateStatus(t.id, 'COMPLETED')}
                        >
                          <CheckCircle2 size={15} />
                          <span>{language === 'ta' ? 'அதிகாரப்பூர்வ சமர்ப்பிப்பை உறுதிசெய்' : 'Record Portal Submission'}</span>
                        </button>
                      )}

                      {/* View Application Pre-fill & Checklist Sheet */}
                      {isCompleted ? (
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => setActiveCertTask(t)}
                          style={{
                            background: '#0f3460',
                            fontSize: '0.88rem',
                            fontWeight: 700,
                            padding: '0.55rem 1.25rem',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                          }}
                        >
                          <FileText size={16} />
                          <span>{language === 'ta' ? 'விண்ணப்ப விவரத் தாள் (Pre-fill Sheet)' : 'View Pre-fill Sheet'}</span>
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          onClick={() => setActiveCertTask(t)}
                          style={{ fontSize: '0.82rem', padding: '0.45rem 0.85rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                        >
                          <FileText size={14} />
                          <span>{language === 'ta' ? 'விவரத் தாள் (Pre-fill Sheet)' : 'Pre-fill Sheet'}</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Citizen Privacy & Data Sovereignty Box (DPDP Act 2023) */}
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '1rem', padding: '2rem', boxShadow: '0 4px 15px rgba(15, 52, 96, 0.05)' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f3460', marginBottom: '0.5rem' }}>
          {language === 'ta' ? 'தனிநபர் தரவு பாதுகாப்பு & உரிமைகள் (சட்ட ஆலோசனைக்கு உட்பட்டது)' : 'Citizen Data Sovereignty & Rights (Pending Legal Review)'}
        </h3>
        <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1.5rem', lineHeight: '1.6' }}>
          {language === 'ta'
            ? 'உங்கள் தரவு உங்கள் உரிமை. எந்த நேரத்திலும் உங்கள் பணிகள், ஆவணங்கள் மற்றும் தகவல்களை முழுமையாக பதிவிறக்கலாம் அல்லது கணக்கை நிரந்தரமாக அழிக்கலாம் (சட்ட ஆலோசனைக்கு உட்பட்டது).'
            : 'Export your complete audit profile or permanently delete all data at any moment (subject to pending legal review).'}
        </p>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleExportData}
            disabled={exporting}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '0.65rem 1.25rem' }}
          >
            <Download size={16} />
            <span>{exporting ? 'Exporting...' : 'Export My Data (JSON)'}</span>
          </button>

          <button
            type="button"
            onClick={handleDeleteData}
            style={{
              background: '#fee2e2',
              color: '#dc2626',
              border: '1px solid #fca5a5',
              padding: '0.65rem 1.25rem',
              borderRadius: '6px',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Trash2 size={16} />
            <span>Permanently Erase Account & All Data</span>
          </button>
        </div>
      </div>

      {/* Official Certificate Modal */}
      {activeCertTask && (
        <OfficialCertificateModal
          task={activeCertTask}
          user={user}
          language={(language === 'en' ? 'en' : 'ta')}
          onClose={() => setActiveCertTask(null)}
        />
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { CheckSquare, ArrowRight, Download, Trash2, Clock, Upload, CheckCircle2, AlertCircle } from 'lucide-react';
import { ApiClient } from '../services/api';
import type { UserTask, UserProfile } from '../types';

interface CitizenDashboardProps {
  language: string;
  user: UserProfile;
  onSelectService: () => void;
}

export const CitizenDashboard: React.FC<CitizenDashboardProps> = ({
  language,
  user,
  onSelectService,
}) => {
  const [tasks, setTasks] = useState<UserTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

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
      setMessage('Your personal data archive was exported successfully in compliance with DPDP Act 2023.');
    } catch (err: any) {
      setMessage(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteData = async () => {
    if (window.confirm('Are you absolutely sure you want to permanently erase your account, all application tasks, and document metadata? This action is irreversible under the DPDP Act.')) {
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
      await ApiClient.updateTaskStatus(taskId, newStatus, 'Citizen completed step');
      loadTasks();
    } catch (err: any) {
      alert(`Cannot advance state: ${err.message}`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span style={{ background: '#d1fae5', color: '#059669', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>COMPLETED</span>;
      case 'READY_TO_SUBMIT':
        return <span style={{ background: '#fef3c7', color: '#b45309', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>READY TO SUBMIT</span>;
      case 'COLLECTING_DOCUMENTS':
        return <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>COLLECTING DOCS</span>;
      default:
        return <span style={{ background: '#f1f5f9', color: '#475569', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700 }}>{status}</span>;
    }
  };

  return (
    <div>
      {/* Welcome Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.75rem', marginBottom: '2rem', boxShadow: 'var(--shadow-sm)' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--primary)', marginBottom: '0.35rem' }}>
            {language === 'ta' ? `வணக்கம், ${user.full_name}!` : `Welcome back, ${user.full_name}!`}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            {language === 'ta'
              ? 'உங்கள் அரசு சேவை விண்ணப்பங்களின் தற்போதைய நிலையை இங்கு கண்காணிக்கலாம்.'
              : 'Track active application workflows, complete required documents, and manage privacy settings.'}
          </p>
        </div>

        <button type="button" className="btn-primary" onClick={onSelectService}>
          <span>{language === 'ta' ? 'புதிய சேவை தொடங்குக' : 'Start New Application'}</span>
          <ArrowRight size={15} />
        </button>
      </div>

      {message && (
        <div style={{ padding: '0.75rem 1.25rem', background: '#d1fae5', color: '#065f46', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={16} />
          <span>{message}</span>
        </div>
      )}

      {/* Tasks Section */}
      <div style={{ marginBottom: '2.5rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '1rem' }}>
          {language === 'ta' ? 'செயலில் உள்ள பணிகள் (Active Tasks)' : 'Active Application Tasks'} ({tasks.length})
        </h3>

        {tasks.length === 0 ? (
          <div style={{ textAlign: 'center', background: 'white', padding: '3rem 2rem', borderRadius: 'var(--radius-lg)', border: '1px dashed var(--border-color)' }}>
            <CheckSquare size={36} color="#94a3b8" style={{ margin: '0 auto 1rem' }} />
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
              {language === 'ta' ? 'தற்போது பணிகள் ஏதுமில்லை' : 'No active application tasks'}
            </h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              {language === 'ta' ? 'சாதி, வருமானம் அல்லது கல்வி உதவித்தொகை விண்ணப்பங்களை இப்போது தொடங்கவும்.' : 'Select a verified service or ask the AI assistant to initiate a guided application.'}
            </p>
            <button type="button" className="btn-primary" onClick={onSelectService}>
              <span>{language === 'ta' ? 'சேவை பட்டியலைப் பார்க்கவும்' : 'Browse Services'}</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {tasks.map((t) => (
              <div
                key={t.id}
                style={{
                  background: 'white',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.5rem',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div>
                    <h4 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--primary)', marginBottom: '0.2rem' }}>
                      {t.service_id.replace(/_/g, ' ').toUpperCase()}
                    </h4>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Task ID: {t.id} • Initiated: {new Date(t.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  {getStatusBadge(t.status)}
                </div>

                {/* Next Action Banner */}
                <div style={{ background: '#f8fafc', padding: '0.85rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0', marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>
                    Recommended Next Action
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#1e293b' }}>
                    {language === 'ta' ? t.next_action_ta : t.next_action_en}
                  </div>
                </div>

                {/* State advancement buttons */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                  {t.status === 'COLLECTING_DOCUMENTS' && (
                    <button
                      type="button"
                      className="btn-primary"
                      style={{ fontSize: '0.82rem', padding: '0.45rem 0.9rem' }}
                      onClick={() => handleUpdateStatus(t.id, 'READY_FOR_USER_REVIEW')}
                    >
                      <CheckCircle2 size={14} />
                      <span>Mark Documents Ready</span>
                    </button>
                  )}
                  {t.status === 'READY_FOR_USER_REVIEW' && (
                    <button
                      type="button"
                      className="btn-primary"
                      style={{ fontSize: '0.82rem', padding: '0.45rem 0.9rem' }}
                      onClick={() => handleUpdateStatus(t.id, 'READY_TO_SUBMIT')}
                    >
                      <CheckCircle2 size={14} />
                      <span>Confirm Verified Details</span>
                    </button>
                  )}
                  {t.status === 'READY_TO_SUBMIT' && (
                    <button
                      type="button"
                      className="btn-primary"
                      style={{ fontSize: '0.82rem', padding: '0.45rem 0.9rem', background: '#059669' }}
                      onClick={() => handleUpdateStatus(t.id, 'SUBMITTED')}
                    >
                      <CheckCircle2 size={14} />
                      <span>Record Official Submission</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Citizen Privacy & Data Sovereignty Box */}
      <div style={{ background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.75rem', boxShadow: 'var(--shadow-sm)' }}>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
          {language === 'ta' ? 'தனிநபர் தரவு பாதுகாப்பு & கட்டுப்பாடுகள் (DPDP Act 2023)' : 'Citizen Data Sovereignty & DPDP Rights'}
        </h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: '1.5' }}>
          {language === 'ta'
            ? 'உங்கள் தரவு உங்கள் உரிமை. எந்த நேரத்திலும் உங்கள் பணிகள், ஆவணங்கள் மற்றும் தகவல்களை முழுமையாக பதிவிறக்கலாம் அல்லது கணக்கை அழிக்கலாம்.'
            : 'You have full legal sovereignty over your records under India’s Digital Personal Data Protection Act. Export your complete audit profile or permanently delete all data at any moment.'}
        </p>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleExportData}
            disabled={exporting}
          >
            <Download size={16} />
            <span>{exporting ? 'Exporting...' : 'Export My Data (JSON)'}</span>
          </button>

          <button
            type="button"
            style={{ background: '#fee2e2', color: '#dc2626', border: '1px solid #fca5a5', padding: '0.65rem 1.25rem', borderRadius: 'var(--radius-md)', fontWeight: 600, fontFamily: 'inherit', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            onClick={handleDeleteData}
          >
            <Trash2 size={16} />
            <span>Permanently Erase Account & All Data</span>
          </button>
        </div>
      </div>
    </div>
  );
};

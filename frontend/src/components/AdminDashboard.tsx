import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle2, Users, FileText, Activity, Clock } from 'lucide-react';
import { ApiClient } from '../services/api';

export const AdminDashboard: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [pbData, metData, auditData] = await Promise.all([
        ApiClient.getAdminPlaybooks(),
        ApiClient.getAdminMetrics(),
        ApiClient.getAuditLogs()
      ]);
      setPlaybooks(pbData);
      setMetrics(metData);
      setAuditLogs(auditData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (serviceId: string, newStatus: string) => {
    try {
      await ApiClient.updatePlaybookStatus(serviceId, newStatus, 'Status updated via Admin Review Panel');
      loadAdminData();
    } catch (err: any) {
      alert(`Error updating playbook: ${err.message}`);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h2 className="section-title" style={{ fontSize: '1.75rem', marginBottom: '0.4rem' }}>
          Civic Knowledge & Playbook Administration
        </h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Review official sources, monitor verification status, inspect audit events, and manage playbook lifecycles.
        </p>
      </div>

      {/* Aggregate Metrics Cards */}
      {metrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2.5rem' }}>
          <div style={{ background: 'white', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Active Playbooks</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--primary)' }}>{metrics.total_playbooks_in_catalog}</div>
          </div>
          <div style={{ background: 'white', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Registered Citizens</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#0284c7' }}>{metrics.total_citizens_registered}</div>
          </div>
          <div style={{ background: 'white', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Application Workflows</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#059669' }}>{metrics.total_application_tasks}</div>
          </div>
          <div style={{ background: 'white', padding: '1.25rem', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Documents Processed</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#d97706' }}>{metrics.total_documents_analyzed}</div>
          </div>
        </div>
      )}

      {/* Playbook Review Queue */}
      <div style={{ background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.75rem', marginBottom: '2.5rem', boxShadow: 'var(--shadow-sm)' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)', marginBottom: '1.25rem' }}>
          Service Playbooks Verification Queue
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '0.75rem' }}>Service ID</th>
                <th style={{ padding: '0.75rem' }}>Title (English / Tamil)</th>
                <th style={{ padding: '0.75rem' }}>Department</th>
                <th style={{ padding: '0.75rem' }}>Official Sources</th>
                <th style={{ padding: '0.75rem' }}>Status</th>
                <th style={{ padding: '0.75rem' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {playbooks.map((pb) => (
                <tr key={pb.service_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.75rem', fontWeight: 700, color: 'var(--primary)' }}>{pb.service_id}</td>
                  <td style={{ padding: '0.75rem' }}>
                    <div style={{ fontWeight: 600 }}>{pb.name_en}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{pb.name_ta}</div>
                  </td>
                  <td style={{ padding: '0.75rem', color: '#475569' }}>{pb.department}</td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600 }}>
                      {pb.official_sources?.length || 0} Sources
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{
                      background: pb.verification_status === 'VERIFIED' ? '#d1fae5' : '#fef3c7',
                      color: pb.verification_status === 'VERIFIED' ? '#059669' : '#b45309',
                      padding: '0.2rem 0.6rem',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 700
                    }}>
                      {pb.verification_status}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <select
                      value={pb.verification_status}
                      onChange={(e) => handleStatusChange(pb.service_id, e.target.value)}
                      style={{ padding: '0.35rem 0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontSize: '0.8rem', fontFamily: 'inherit' }}
                    >
                      <option value="DRAFT">DRAFT</option>
                      <option value="NEEDS_VERIFICATION">NEEDS VERIFICATION</option>
                      <option value="VERIFIED">VERIFIED</option>
                      <option value="RETIRED">RETIRED</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Security Audit Events */}
      <div style={{ background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.75rem', boxShadow: 'var(--shadow-sm)' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)', marginBottom: '1.25rem' }}>
          Security & Access Audit Trail (DPDP Compliance)
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          {auditLogs.slice(0, 10).map((log) => (
            <div
              key={log.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.65rem 1rem',
                background: '#f8fafc',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid #e2e8f0',
                fontSize: '0.82rem'
              }}
            >
              <div>
                <span style={{ fontWeight: 700, color: 'var(--primary)', marginRight: '8px' }}>[{log.action}]</span>
                <span style={{ color: '#475569' }}>Resource: {log.resource_type || 'SYSTEM'}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
                <Clock size={13} />
                <span>{new Date(log.timestamp).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

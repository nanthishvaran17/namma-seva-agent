import React, { useState } from 'react';
import { X, Lock, Mail, User, Phone, ShieldCheck } from 'lucide-react';
import { ApiClient } from '../services/api';
import type { UserProfile } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: UserProfile) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [consentGranted, setConsentGranted] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        if (!consentGranted) {
          throw new Error('Please agree to DPDP processing of application assistance data.');
        }
        const res = await ApiClient.register({
          email,
          password,
          full_name: fullName,
          phone_number: phone,
          preferred_language: 'ta'
        });
        onSuccess(res.user);
      } else {
        const res = await ApiClient.login({ email, password });
        onSuccess(res.user);
      }
      onClose();
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--primary)' }}>
            {isRegister ? 'குடிமக்கள் பதிவு (Citizen Registration)' : 'உள்நுழைவு (Citizen Login)'}
          </h3>
          <button type="button" onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ padding: '0.65rem 1rem', background: '#fee2e2', color: '#dc2626', borderRadius: 'var(--radius-sm)', fontSize: '0.82rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isRegister && (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.35rem' }}>
                முழுப் பெயர் (Full Name)
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ravi Kumar"
                style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontFamily: 'inherit' }}
              />
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.35rem' }}>
              மின்னஞ்சல் (Email Address)
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="citizen@example.com"
              style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontFamily: 'inherit' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.35rem' }}>
              கடவுச்சொல் (Password)
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontFamily: 'inherit' }}
            />
          </div>

          {isRegister && (
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.35rem' }}>
                கைபேசி எண் (Phone Number - விருப்பமானது)
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="9876543210"
                style={{ width: '100%', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', fontFamily: 'inherit' }}
              />
            </div>
          )}

          {isRegister && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              <input
                type="checkbox"
                id="dpdp-consent"
                checked={consentGranted}
                onChange={(e) => setConsentGranted(e.target.checked)}
                style={{ marginTop: '3px' }}
              />
              <label htmlFor="dpdp-consent">
                DPDP சட்டம் 2023 படி, அரசு சேவை வழிகாட்டுதலுக்காக எனது ஆவணங்கள் மற்றும் தகவல்களை பரிசீலிக்க ஒப்புதல் அளிக்கிறேன்.
              </label>
            </div>
          )}

          <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '0.5rem' }} disabled={loading}>
            <span>{loading ? 'Processing...' : isRegister ? 'பதிவு செய்க (Sign Up)' : 'உள்நுழைக (Sign In)'}</span>
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.25rem', fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>
            {isRegister ? 'ஏற்கனவே கணக்கு உள்ளதா? ' : 'புதிய பயனரா? '}
          </span>
          <button
            type="button"
            style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit' }}
            onClick={() => setIsRegister(!isRegister)}
          >
            {isRegister ? 'உள்நுழைக (Sign In)' : 'இலவசமாக பதிவு செய்க (Sign Up)'}
          </button>
        </div>
      </div>
    </div>
  );
};

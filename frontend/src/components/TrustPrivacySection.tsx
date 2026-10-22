import React, { useState } from 'react';
import { ShieldCheck, Lock, EyeOff, FileText, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';

interface TrustPrivacySectionProps {
  language: string;
}

export const TrustPrivacySection: React.FC<TrustPrivacySectionProps> = ({ language }) => {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const faqs = [
    {
      q_ta: 'நம்ம சேவை தளம் உண்மையான தமிழ்நாடு அரசு தளமா?',
      q_en: 'Is Namma Seva Agent an official government entity?',
      a_ta: 'நம்ம சேவை என்பது குடிமக்களுக்கு அரசு சேவைகளை எளிதாக்க உருவாக்கப்பட்ட ஒரு வெளிப்படையான AI வழிகாட்டி தளமாகும். அனைத்து தகவல்களும் தமிழ்நாடு அரசின் அதிகாரப்பூர்வ e-Sevai, வருவாய்த் துறை மற்றும் நலத்துறை ஆவணங்கள் மூலம் சரிபார்க்கப்பட்டு ஆதாரங்களுடன் வழங்கப்படுகின்றன.',
      a_en: 'Namma Seva Agent is an independent civic assistance platform designed to make government services accessible. Every rule, fee, and timeline is grounded directly in verified government documentation from TNeGA, Revenue Dept, and official welfare portals with full citations.'
    },
    {
      q_ta: 'என் ஆவணங்கள் மற்றும் தகவல்கள் பாதுகாப்பாக இருக்குமா?',
      q_en: 'Are my uploaded documents and information safe?',
      a_ta: 'ஆம். டிஜிட்டல் தனிநபர் தரவு பாதுகாப்புச் சட்டம் (DPDP Act 2023) படி, உங்கள் ஆவணங்கள் பிரத்யேகமாக என்க்ரிப்ட் செய்யப்பட்டு சேமிக்கப்படுகின்றன. உங்கள் ஒப்புதல் இன்றி யாருடனும் பகிரப்படாது. எந்த நேரத்திலும் உங்கள் தரவை முழுமையாக பதிவிறக்கவோ அல்லது நிரந்தரமாக அழிக்கவோ உரிமை உண்டு.',
      a_en: 'Yes. In strict alignment with the Digital Personal Data Protection (DPDP) Act 2023, all documents are encrypted at rest and in transit. Your documents are used solely for your active application guidance and can be permanently deleted with one click.'
    },
    {
      q_ta: 'AI தளம் எனது சார்பாக நேரடியாக விண்ணப்பம் சமர்ப்பிக்குமா?',
      q_en: 'Does the AI autonomously submit my application?',
      a_ta: 'இல்லை. பாதுகாப்புக் கொள்கையின்படி, நாங்கள் OTP, கடவுச்சொற்கள் (Passwords) அல்லது வங்கிக் கணக்கு ரகசியங்களை ஒருபோதும் கேட்க மாட்டோம். தேவையான ஆவணங்களை சரிபார்த்து, அதிகாரப்பூர்வ இ-சேவை தளத்தில் நீங்களே எளிதாக விண்ணப்பிக்க வழிகாட்டுவோம் (Guided Submission).',
      a_en: 'No. To ensure absolute citizen safety and comply with portal access policies, we strictly NEVER ask for, store, or accept citizen OTPs or portal passwords. We guide you step-by-step through the official portal so you remain in 100% control.'
    }
  ];

  return (
    <section style={{ marginTop: '3.5rem', marginBottom: '3rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <h2 className="section-title" style={{ fontSize: '1.85rem' }}>
          {language === 'ta' ? 'பாதுகாப்பு & வெளிப்படைத்தன்மை' : 'Trust, Privacy & Civic Integrity'}
        </h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: '640px', margin: '0.5rem auto 0' }}>
          {language === 'ta'
            ? 'குடிமக்களின் பாதுகாப்பு மற்றும் தகவல்களின் துல்லியம் எங்களின் முதன்மையான முன்னுரிமை.'
            : 'Engineered with strict data privacy boundaries, verified official sources, and zero sensitive data disclosure.'}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        <div style={{ background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: '#d1fae5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <ShieldCheck size={22} />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {language === 'ta' ? 'சரிபார்க்கப்பட்ட ஆதாரங்கள்' : '100% Verified Sources'}
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            {language === 'ta'
              ? 'அனைத்து கட்டணங்கள், கால அவகாசங்கள் மற்றும் ஆவணப் பட்டியல்கள் .tn.gov.in அதிகாரப்பூர்வ அரசு அறிவிப்புகள் மூலம் சரிபார்க்கப்பட்டவை.'
              : 'Every fee, rule, and deadline is anchored to published Tamil Nadu Government Citizen Charters and gazettes.'}
          </p>
        </div>

        <div style={{ background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <EyeOff size={22} />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {language === 'ta' ? 'OTP & கடவுச்சொல் பாதுகாப்பு' : 'Zero OTP / Password Policy'}
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            {language === 'ta'
              ? 'நாங்கள் ஒருபோதும் ஆதார் OTP அல்லது இ-சேவை கடவுச்சொற்களை கேட்க மாட்டோம். சமர்ப்பிப்பு உங்கள் கட்டுப்பாட்டில் மட்டுமே நடக்கும்.'
              : 'The agent strictly never asks for or handles citizen OTPs, passwords, or CAPTCHA answers. Submission remains under your direct control.'}
          </p>
        </div>

        <div style={{ background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.5rem', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: '#ede9fe', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <Lock size={22} />
          </div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            {language === 'ta' ? 'DPDP சட்டம் 2023 உரிமைகள்' : 'DPDP Act 2023 Compliance'}
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            {language === 'ta'
              ? 'ஒரே கிளிக்கில் உங்கள் தனிப்பட்ட தகவல்களை பதிவிறக்கம் செய்யவோ அல்லது நிரந்தரமாக அழிக்கவோ முழு உரிமை உள்ளது.'
              : 'Citizen data sovereignty is built-in. Download your complete data archive or execute permanent erasure at any time.'}
          </p>
        </div>
      </div>

      {/* FAQ Accordion */}
      <div style={{ maxWidth: '800px', margin: '0 auto', background: 'white', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)', padding: '1.75rem', boxShadow: 'var(--shadow-sm)' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '1.25rem', color: 'var(--primary)' }}>
          {language === 'ta' ? 'அடிக்கடி கேட்கப்படும் கேள்விகள் (FAQ)' : 'Frequently Asked Questions'}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div key={idx} style={{ borderBottom: idx < faqs.length - 1 ? '1px solid var(--border-color)' : 'none', paddingBottom: '0.75rem' }}>
                <button
                  type="button"
                  style={{ width: '100%', background: 'none', border: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit', fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)' }}
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                >
                  <span>{language === 'ta' ? faq.q_ta : faq.q_en}</span>
                  {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {isOpen && (
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '0.4rem', lineHeight: '1.6' }}>
                    {language === 'ta' ? faq.a_ta : faq.a_en}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

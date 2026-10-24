import React, { useState } from 'react';
import { Search, ArrowRight, ShieldCheck, Mic, MicOff, Camera, Sparkles } from 'lucide-react';
import { InstagramStories } from './InstagramStories';

interface HeroSearchProps {
  language: string;
  onSearch: (query: string) => void;
  onSelectStoryService?: (serviceId: string) => void;
}

export const HeroSearch: React.FC<HeroSearchProps> = ({ language, onSearch, onSelectStoryService }) => {
  const [inputVal, setInputVal] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [showScanNotice, setShowScanNotice] = useState(false);

  const handleStartVoice = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }

    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRec) {
      try {
        const recognition = new SpeechRec();
        recognition.lang = language === 'ta' ? 'ta-IN' : 'en-IN';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        setIsListening(true);

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInputVal(transcript);
          setIsListening(false);
          if (transcript.trim()) {
            setTimeout(() => onSearch(transcript), 400);
          }
        };

        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);
        recognition.start();
      } catch {
        setIsListening(false);
      }
    } else {
      setIsListening(true);
      setTimeout(() => {
        const sampleQuery = language === 'ta' ? 'சாதிச் சான்றிதழ் பெற என்ன ஆவணங்கள் தேவை?' : 'How to apply for income certificate?';
        setInputVal(sampleQuery);
        setIsListening(false);
        setTimeout(() => onSearch(sampleQuery), 400);
      }, 2000);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputVal.trim()) {
      onSearch(inputVal.trim());
    }
  };

  const quickFilterPills = [
    { label: language === 'ta' ? '📜 சாதிச் சான்றிதழ்' : 'Community Cert', query: 'சாதிச் சான்றிதழ் பெற என்ன ஆவணங்கள் தேவை?' },
    { label: language === 'ta' ? '💰 வருமானச் சான்றிதழ்' : 'Income Cert', query: 'வருமானச் சான்றிதழ் பெற எப்படி விண்ணப்பிப்பது?' },
    { label: language === 'ta' ? '🎓 முதல் பட்டதாரி சலுகை' : 'First Graduate', query: 'First graduate certificate eligibility in Tamil Nadu' },
    { label: language === 'ta' ? '💵 கல்வி உதவித்தொகை' : 'Scholarships', query: 'Post matric scholarship eligibility and income limits' },
    { label: language === 'ta' ? '🍚 ரேஷன் அட்டை' : 'Smart Ration Card', query: 'Smart ration card new application' },
    { label: language === 'ta' ? '👩‍💼 மகளிர் உரிமைத் தொகை' : 'Magalir Urimai', query: 'Magalir Urimai Thogai 1000 eligibility guidelines' },
  ];

  return (
    <section className="phonepe-hero-wrapper">
      {/* 1. Quick Reels / Visual Guides at Top */}
      <div className="phonepe-stories-container">
        <InstagramStories
          language={language}
          onSelectStoryService={(svcId) => {
            if (onSelectStoryService) {
              onSelectStoryService(svcId);
            } else {
              onSearch(`Tell me requirements, checklist, and eligibility for ${svcId}`);
            }
          }}
        />
      </div>

      {/* 2. Main PhonePe / Google Pay Style Friendly Banner */}
      <div className="phonepe-hero-card">
        <div className="phonepe-welcome-tag">
          <ShieldCheck size={16} color="#0071e3" />
          <span>{language === 'ta' ? 'தமிழ்நாடு அரசின் அதிகாரப்பூர்வ AI வழிகாட்டி' : 'Tamil Nadu Government AI Civic Assistant'}</span>
        </div>

        <h1 className="phonepe-hero-title">
          {language === 'ta' ? (
            <>
              அரசு சேவைகளை எளிதாகப் பெற <br />
              <span className="phonepe-gradient-text">உங்கள் சொந்த மொழியில் கேளுங்கள்!</span>
            </>
          ) : (
            <>
              Tamil Nadu Civic Services, <br />
              <span className="phonepe-gradient-text">Simple as Google Pay.</span>
            </>
          )}
        </h1>

        <p className="phonepe-hero-subtitle">
          {language === 'ta'
            ? 'சாதி, வருமானம், இருப்பிடம், முதல் பட்டதாரி சான்றிதழ்கள் மற்றும் கல்வி உதவித்தொகைகளுக்கு என்ன ஆவணங்கள் தேவை என்பதை நொடிகளில் அறியலாம்.'
            : 'Check eligibility, auto-generate official document checklists, and complete applications with 1-click ease.'}
        </p>

        {/* Big Touch-Friendly Search & Speak Bar */}
        <form className="phonepe-search-bar" onSubmit={handleFormSubmit}>
          <Search className="phonepe-search-icon" size={22} />
          <input
            type="text"
            className="phonepe-search-input"
            placeholder={
              isListening
                ? language === 'ta'
                  ? '🎙️ பேசுங்கள்... உங்கள் குரலைக் கேட்கிறது...'
                  : '🎙️ Listening... Please speak your question...'
                : language === 'ta'
                ? 'உங்களுக்கு என்ன சான்றிதழ் தேவை? (எ.கா: சாதி சான்றிதழ்)'
                : 'What civic service do you need? (e.g. Income certificate, First graduate)'
            }
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
          />

          <div className="phonepe-search-actions">
            {/* Big Voice Mic Button */}
            <button
              type="button"
              className={`phonepe-mic-btn ${isListening ? 'listening' : ''}`}
              onClick={handleStartVoice}
              title={language === 'ta' ? 'பேசித் தேடவும்' : 'Speak to search'}
            >
              {isListening ? <MicOff size={20} color="#ff3b30" /> : <Mic size={20} color="#0071e3" />}
              <span className="mic-btn-text">{language === 'ta' ? 'பேசுங்கள்' : 'Speak'}</span>
            </button>

            <button
              type="button"
              className="phonepe-scan-btn"
              onClick={() => setShowScanNotice(true)}
              title={language === 'ta' ? 'ஆவண ஸ்கேனர்' : 'Scan documents'}
            >
              <Camera size={18} color="#86868b" />
            </button>

            <button type="submit" className="phonepe-search-btn">
              <span>{language === 'ta' ? 'தேடுக' : 'Search'}</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </form>

        {/* Listening Animation Indicator */}
        {isListening && (
          <div className="phonepe-listening-indicator">
            <span className="pulse-dot" />
            <span>{language === 'ta' ? 'கேட்கிறது... தமிழில் பேசலாம்...' : 'Listening... Speak in Tamil or English...'}</span>
          </div>
        )}

        {/* Popular Quick Filter Pills */}
        <div className="phonepe-pills-row">
          <span className="phonepe-pills-label">
            {language === 'ta' ? 'அடிக்கடி கேட்கப்படும் கேள்விகள்:' : 'Quick shortcuts:'}
          </span>
          <div className="phonepe-pills-scroll">
            {quickFilterPills.map((p, i) => (
              <button
                key={i}
                type="button"
                className="phonepe-shortcut-pill"
                onClick={() => onSearch(p.query)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Scanner Notice Modal */}
      {showScanNotice && (
        <div className="phonepe-modal-backdrop" onClick={() => setShowScanNotice(false)}>
          <div className="phonepe-modal-sheet" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '440px', textAlign: 'center' }}>
            <div className="phonepe-scan-icon-circle">
              <Camera size={32} color="#0071e3" />
            </div>
            <h3 className="phonepe-modal-heading" style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
              {language === 'ta' ? 'ஆவண சரிபார்ப்பு ஸ்கேனர்' : 'Document Scanner & OCR'}
            </h3>
            <p className="phonepe-modal-desc" style={{ marginBottom: '1.5rem' }}>
              {language === 'ta'
                ? 'உங்கள் ஆதார் அட்டை, ரேஷன் அட்டை அல்லது பள்ளி மாற்றுச் சான்றிதழைப் பதிவேற்றி, பெயர் மற்றும் விவரங்கள் அரசு பதிவேடுகளுடன் சரியாக உள்ளதா என AI மூலம் நொடிகளில் சரிபார்க்கலாம்.'
                : 'Upload your Aadhaar or Ration Card to automatically verify spelling and certificate prerequisites with zero errors.'}
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                className="phonepe-primary-btn"
                onClick={() => {
                  setShowScanNotice(false);
                  onSearch('Verify my documents checklist and spelling consistency');
                }}
              >
                {language === 'ta' ? 'சரிபார்க்கத் தொடங்கு' : 'Start Verification'}
              </button>
              <button
                className="phonepe-share-btn"
                onClick={() => setShowScanNotice(false)}
              >
                {language === 'ta' ? 'மூடுக' : 'Close'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

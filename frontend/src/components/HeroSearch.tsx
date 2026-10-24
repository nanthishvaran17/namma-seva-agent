import React, { useState } from 'react';
import { Search, ArrowRight, Mic, MicOff, Sparkles } from 'lucide-react';

interface HeroSearchProps {
  language: string;
  onSearch: (query: string) => void;
  onSelectStoryService?: (serviceId: string) => void;
}

export const HeroSearch: React.FC<HeroSearchProps> = ({ language, onSearch }) => {
  const [inputVal, setInputVal] = useState('');
  const [isListening, setIsListening] = useState(false);

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
      {/* Friendly Welcome Card */}
      <div className="phonepe-hero-card">
        <div className="phonepe-welcome-tag">
          <Sparkles size={16} color="#0071e3" />
          <span>{language === 'ta' ? 'அரசு இ-சேவை AI நேரடி வழிகாட்டி' : 'TN Government AI Civic Guide'}</span>
        </div>

        <h1 className="phonepe-hero-title">
          {language === 'ta' ? (
            <>
              வணக்கம்! இன்று உங்களுக்கு <br />
              <span className="phonepe-gradient-text">என்ன சான்றிதழ் உதவி வேண்டும்?</span>
            </>
          ) : (
            <>
              Hello! Which civic service <br />
              <span className="phonepe-gradient-text">can we assist you with today?</span>
            </>
          )}
        </h1>

        <p className="phonepe-hero-subtitle">
          {language === 'ta'
            ? 'சாதி, வருமானம், ரேஷன், முதல் பட்டதாரி — தேவையான ஆவணங்கள் மற்றும் வழிகாட்டுதலை நொடிகளில் அறியலாம்.'
            : 'Check eligibility, 3 mandatory documents, fee & step-by-step guidance in seconds.'}
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
                  ? '🎙️ கேட்கிறது... தமிழில் பேசலாம்...'
                  : '🎙️ Listening... Please speak now...'
                : language === 'ta'
                ? 'உங்களுக்கு என்ன உதவி வேண்டும்? (எ.கா: சாதிச் சான்றிதழ்)'
                : 'Ask anything (e.g., Community certificate requirements)'
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
              {isListening ? <MicOff size={18} color="#ff3b30" /> : <Mic size={18} color="#0071e3" />}
              <span className="mic-btn-text">{language === 'ta' ? 'பேசுங்கள்' : 'Speak'}</span>
            </button>

            <button type="submit" className="phonepe-search-btn">
              <span>{language === 'ta' ? 'கேளுங்கள்' : 'Ask AI'}</span>
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
            {language === 'ta' ? 'விரைவு தேர்வுகள்:' : 'Quick shortcuts:'}
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
    </section>
  );
};

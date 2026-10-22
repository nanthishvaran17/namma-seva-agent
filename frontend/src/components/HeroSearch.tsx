import React, { useState } from 'react';
import { Search, Sparkles, ArrowRight, Shield } from 'lucide-react';

interface HeroSearchProps {
  language: string;
  onSearch: (query: string) => void;
}

export const HeroSearch: React.FC<HeroSearchProps> = ({ language, onSearch }) => {
  const [inputVal, setInputVal] = useState('');

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputVal.trim()) {
      onSearch(inputVal.trim());
    }
  };

  const chips = [
    { label: 'சாதிச் சான்றிதழ் (Community Certificate)', query: 'சாதிச் சான்றிதழ் பெற என்ன ஆவணங்கள் தேவை?' },
    { label: 'வருமானச் சான்றிதழ் (Income Certificate)', query: 'வருமானச் சான்றிதழ் பெற எப்படி விண்ணப்பிப்பது?' },
    { label: 'முதல் தலைமுறை பட்டதாரி (First Graduate)', query: 'First graduate certificate eligibility in Tamil Nadu' },
    { label: 'BC / SC Scholarship', query: 'Enakku BC scholarship apply pannanum' },
    { label: 'இருப்பிடச் சான்றிதழ் (Nativity Certificate)', query: 'Nativity certificate continuous residence rules' },
  ];

  return (
    <section className="hero-box">
      <div className="hero-tag">
        <Shield size={15} />
        <span>
          {language === 'ta'
            ? 'அங்கீகரிக்கப்பட்ட அரசு வழிகாட்டி — 100% அதிகாரப்பூர்வ தகவல்கள்'
            : 'Verified Civic Assistant — 100% Official Source Grounded'}
        </span>
      </div>

      <h1 className="hero-title">
        {language === 'ta' ? (
          <>
            அரசு சேவைகளை எளிதாகப் பெற <br />
            <span style={{ color: '#ffb74d' }}>உங்கள் சொந்த மொழியில் கேளுங்கள்</span>
          </>
        ) : (
          <>
            Access Tamil Nadu Government Services <br />
            <span style={{ color: '#ffb74d' }}>In Simple Tamil, Tanglish & English</span>
          </>
        )}
      </h1>

      <p className="hero-subtitle">
        {language === 'ta'
          ? 'சாதி, வருமானம், இருப்பிடம், முதல் பட்டதாரி சான்றிதழ்கள் மற்றும் கல்வி உதவித்தொகைகளுக்கு என்ன ஆவணங்கள் தேவை, எப்படி விண்ணப்பிக்க வேண்டும் என்பதை துல்லியமாக அறிந்து கொள்ளுங்கள்.'
          : 'Discover requirements, resolve prerequisites, prepare document checklists, and track application workflows with an intelligent civic assistant.'}
      </p>

      <form className="search-wrapper" onSubmit={handleFormSubmit}>
        <Search className="search-icon-left" size={20} />
        <input
          type="text"
          className="search-input-box"
          placeholder={
            language === 'ta'
              ? 'உங்களுக்கு என்ன அரசு சேவை தேவை? (எ.கா: எனக்கு சாதிச் சான்றிதழ் வேண்டும்)'
              : 'What service do you need? (e.g. "Enakku income certificate venum" or "First graduate")'
          }
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
        />
        <button type="submit" className="search-action-btn">
          <span>{language === 'ta' ? 'கேளுங்கள்' : 'Ask AI'}</span>
          <ArrowRight size={16} />
        </button>
      </form>

      <div className="prompt-chips">
        {chips.map((c, i) => (
          <button
            key={i}
            type="button"
            className="prompt-chip"
            onClick={() => onSearch(c.query)}
          >
            <Sparkles size={13} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
            {c.label}
          </button>
        ))}
      </div>
    </section>
  );
};

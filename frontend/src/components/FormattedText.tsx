import React from 'react';

interface FormattedTextProps {
  content: string;
}

export const FormattedText: React.FC<FormattedTextProps> = ({ content }) => {
  if (!content) return null;

  const lines = content.split('\n');

  const renderInlineFormatted = (text: string) => {
    // Replace triple asterisks if any
    let cleaned = text.replace(/\*\*\*/g, '**');

    // Split on **bold** pattern
    const parts = cleaned.split(/(\*\*[^*]+?\*\*)/g);

    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const inner = part.slice(2, -2).trim();
        return (
          <strong key={i} style={{ fontWeight: 700, color: 'inherit' }}>
            {inner}
          </strong>
        );
      }
      return part;
    });
  };

  return (
    <div className="formatted-message-container" style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', lineHeight: 1.55 }}>
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} style={{ height: '0.35rem' }} />;
        }

        // Check if line is a bullet item
        const isBullet = /^[•\-\*]\s+/.test(trimmed) || trimmed.startsWith('•');
        // Check if line is a numbered item like "1. "
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);

        if (numMatch) {
          const [, num, rest] = numMatch;
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'baseline', gap: '0.45rem', paddingLeft: '0.2rem' }}>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: '18px',
                  height: '18px',
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: '#059669',
                  fontSize: '0.75rem',
                  fontWeight: 700
                }}
              >
                {num}
              </span>
              <div style={{ flex: 1 }}>{renderInlineFormatted(rest)}</div>
            </div>
          );
        }

        if (isBullet) {
          const bulletText = trimmed.replace(/^[•\-\*]\s*/, '');
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'baseline', gap: '0.45rem', paddingLeft: '0.2rem' }}>
              <span style={{ color: '#059669', fontSize: '1rem', lineHeight: 1 }}>•</span>
              <div style={{ flex: 1 }}>{renderInlineFormatted(bulletText)}</div>
            </div>
          );
        }

        return (
          <div key={idx}>
            {renderInlineFormatted(trimmed)}
          </div>
        );
      })}
    </div>
  );
};

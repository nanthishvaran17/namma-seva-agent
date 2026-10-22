import React from 'react';
import { Award, GraduationCap, Users, Sprout, Briefcase, ShoppingBag, HeartHandshake, Eye, MapPin, Building2 } from 'lucide-react';

interface CategoryExplorerProps {
  language: string;
  onSelectCategory: (catId: string) => void;
}

export const CategoryExplorer: React.FC<CategoryExplorerProps> = ({ language, onSelectCategory }) => {
  const categories = [
    {
      id: 'certificates_revenue',
      title_ta: 'வருவாய்ச் சான்றிதழ்கள்',
      title_en: 'Revenue Certificates',
      desc_ta: 'சாதி, வருமானம், இருப்பிடம், வாரிசுரிமை சான்றிதழ்கள்',
      desc_en: 'Community, Income, Nativity, and Legal Heir certificates',
      icon: <Award size={22} />,
      color: '#0284c7',
      bg: '#e0f2fe'
    },
    {
      id: 'scholarships_education',
      title_ta: 'கல்வி மற்றும் உதவித்தொகை',
      title_en: 'Scholarships & Education',
      desc_ta: 'முதல் பட்டதாரி கட்டண விலக்கு, போஸ்ட் மெட்ரிக் ஸ்காலர்ஷிப்',
      desc_en: 'First Graduate fee waiver, Post-Matric scholarships & grants',
      icon: <GraduationCap size={22} />,
      color: '#d97706',
      bg: '#fef3c7'
    },
    {
      id: 'welfare_social',
      title_ta: 'சமூக நலம் & மகளிர் நலன்',
      title_en: 'Social & Women Welfare',
      desc_ta: 'மகளிர் உரிமைத் தொகை, திருமண நிதியுதவி திட்டங்கள்',
      desc_en: 'Kalaignar Magalir Urimai Thogai, marriage assistance schemes',
      icon: <Users size={22} />,
      color: '#7c3aed',
      bg: '#ede9fe'
    },
    {
      id: 'farmer_agriculture',
      title_ta: 'உழவர் நலன் & வேளாண்மை',
      title_en: 'Agriculture & Farmer Welfare',
      desc_ta: 'பயிர் காப்பீடு, உழவர் அட்டை மற்றும் மானியங்கள்',
      desc_en: 'Crop insurance, farmer registration and seed subsidies',
      icon: <Sprout size={22} />,
      color: '#059669',
      bg: '#d1fae5'
    },
    {
      id: 'ration_civil_supplies',
      title_ta: 'குடும்ப அட்டை (TNPDS)',
      title_en: 'Ration Card & Civil Supplies',
      desc_ta: 'புதிய ஸ்மார்ட் கார்டு, முகவரி மற்றும் உறுப்பினர் திருத்தம்',
      desc_en: 'Smart card application, member addition and changes',
      icon: <ShoppingBag size={22} />,
      color: '#e11d48',
      bg: '#ffe4e6'
    },
    {
      id: 'pensions_senior',
      title_ta: 'முதியோர் & முதியோர் ஓய்வூதியம்',
      title_en: 'Senior Citizen Pensions',
      desc_ta: 'OAP, ஆதரவற்ற விதவை ஓய்வூதியம், முதியோர் நலன்',
      desc_en: 'Old Age Pension, destitute widow and senior support',
      icon: <HeartHandshake size={22} />,
      color: '#475569',
      bg: '#f1f5f9'
    }
  ];

  return (
    <div>
      <div className="section-heading">
        <h2 className="section-title">
          {language === 'ta' ? 'அரசு சேவைகள் பிரிவுகள்' : 'Explore Service Sectors'}
        </h2>
      </div>

      <div className="category-grid">
        {categories.map((cat) => (
          <div
            key={cat.id}
            className="category-card"
            onClick={() => onSelectCategory(cat.id)}
          >
            <div
              className="category-icon-box"
              style={{ backgroundColor: cat.bg, color: cat.color }}
            >
              {cat.icon}
            </div>
            <div className="category-title">
              {language === 'ta' ? cat.title_ta : cat.title_en}
            </div>
            <div className="category-desc">
              {language === 'ta' ? cat.desc_ta : cat.desc_en}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

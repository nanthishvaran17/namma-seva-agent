import React, { useState, useEffect } from 'react';
import { 
  X, ChevronRight, ChevronLeft, Sparkles, CheckCircle2, ArrowRight, FileText, Clock, ShieldCheck,
  GraduationCap, Award, Receipt, ShoppingBag, BookOpen, Heart, Sprout
} from 'lucide-react';

interface Story {
  id: string;
  title_ta: string;
  title_en: string;
  category: string;
  icon: React.ReactNode;
  color: string;
  serviceId: string;
  slides: {
    heading_ta: string;
    heading_en: string;
    sub_ta: string;
    sub_en: string;
    badge: string;
    points_ta: string[];
    points_en: string[];
    fee: string;
    timeline: string;
  }[];
}

interface InstagramStoriesProps {
  language: string;
  onSelectStoryService: (serviceId: string) => void;
}

export const InstagramStories: React.FC<InstagramStoriesProps> = ({ language, onSelectStoryService }) => {
  const [activeStory, setActiveStory] = useState<Story | null>(null);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  const stories: Story[] = [
    {
      id: 'first_grad',
      title_ta: 'முதல் பட்டதாரி',
      title_en: 'First Graduate',
      category: 'கல்வி',
      icon: <GraduationCap size={22} color="white" />,
      color: 'linear-gradient(135deg, #f59e0b, #d97706)',
      serviceId: 'first_graduate_certificate',
      slides: [
        {
          heading_ta: 'முதல் பட்டதாரி சலுகை — யாருக்கு கிடைக்கும்?',
          heading_en: 'First Graduate Fee Waiver — Who is Eligible?',
          sub_ta: 'குடும்பத்தில் நீங்கள் தான் முதல் பட்டதாரியா? தமிழ்நாடு அரசு மூலம் கல்லூரி கல்விக் கட்டணத்தில் முழு சலுகை பெறலாம்.',
          sub_en: 'Are you the first person in your entire family to pursue a degree? Avail full college tuition fee waiver.',
          badge: 'கட்டணச் சலுகை',
          points_ta: [
            'குடும்பத்தில் பெற்றோர், உடன்பிறப்புகள் யாரும் பட்டப்படிப்பு முடித்திருக்கக் கூடாது',
            'அரசு மற்றும் அரசு உதவிபெறும் கல்லூரிகள் & கவுன்சிலிங் ஒதுக்கீட்டுக்கு பொருந்தும்',
            'ஆண்டுக்கு ₹20,000 முதல் ₹25,000 வரை கட்டணக் குறைப்பு'
          ],
          points_en: [
            'No parents or siblings in the immediate family should hold a degree',
            'Applicable for Anna University counselling, Medical & Arts colleges',
            'Direct tuition reduction of ₹20,000 - ₹25,000 per academic year'
          ],
          fee: 'அரசு கட்டணம்: ₹60',
          timeline: 'கிடைக்கும் காலம்: 7-15 நாட்கள்'
        },
        {
          heading_ta: 'தேவையான 4 முக்கிய ஆவணங்கள்',
          heading_en: '4 Essential Documents Required',
          sub_ta: 'இவற்றைப் பதிவேற்ற தயாராக வைத்துக் கொள்ளுங்கள்:',
          sub_en: 'Keep these scanned copies ready for quick processing:',
          badge: 'ஆவணங்கள்',
          points_ta: [
            '1. மாணவரின் 10th / 12th மதிப்பெண் சான்றிதழ்',
            '2. பெற்றோரின் பள்ளி மாற்றுச் சான்றிதழ் (TC) அல்லது படிப்பறிவின்மை உறுதிமொழி',
            '3. உடன்பிறப்புகளின் பள்ளி/கல்லூரி TC அல்லது சான்றிதழ்கள்',
            '4. குடும்ப ஸ்மார்ட் ரேஷன் அட்டை & ஆதார் அட்டை'
          ],
          points_en: [
            '1. Student 10th & 12th Marksheets & Transfer Certificate (TC)',
            '2. Parents School TC or Joint Declaration of no degree',
            '3. Siblings Educational Status proof / TC',
            '4. Family Smart Ration Card & Aadhaar'
          ],
          fee: 'அரசு கட்டணம்: ₹60',
          timeline: 'கிடைக்கும் காலம்: 7-15 நாட்கள்'
        },
        {
          heading_ta: 'எப்படி விண்ணப்பிப்பது? எளிய 3 படிகள்',
          heading_en: 'How to Apply in 3 Simple Steps',
          sub_ta: 'நம்ம சேவை AI வழிகாட்டுதலுடன் உடனடியாக விண்ணப்பிக்கலாம்:',
          sub_en: 'Complete guided submission with verified government checklist:',
          badge: 'விண்ணப்ப முறை',
          points_ta: [
            'படி 1: நம்ம சேவை AI மூலம் தகுதி மற்றும் ஆவணங்களை சரிபார்க்கவும்',
            'படி 2: e-Sevai / tnesevai.tn.gov.in போர்ட்டலில் CAN எண்ணுடன் உள்நுழையவும்',
            'படி 3: VAO மற்றும் RI ஆய்வுக்குப் பின் தாசில்தார் டிஜிட்டல் கையொப்பமிட்ட சான்றிதழ் பெறவும்'
          ],
          points_en: [
            'Step 1: Check eligibility and checklist using Namma Seva AI',
            'Step 2: Sign in to tnesevai.tn.gov.in with CAN registration',
            'Step 3: Receive Tahsildar digitally signed certificate after VAO/RI review'
          ],
          fee: 'அரசு கட்டணம்: ₹60',
          timeline: 'கிடைக்கும் காலம்: 7-15 நாட்கள்'
        }
      ]
    },
    {
      id: 'community_cert',
      title_ta: 'சாதிச் சான்றிதழ்',
      title_en: 'Community Cert',
      category: 'சான்றிதழ்',
      icon: <Award size={22} color="white" />,
      color: 'linear-gradient(135deg, #0284c7, #0369a1)',
      serviceId: 'community_certificate',
      slides: [
        {
          heading_ta: 'சாதிச் சான்றிதழ் — வாழ்நாள் முழுவதும் செல்லும்!',
          heading_en: 'Community Certificate — Lifetime Validity!',
          sub_ta: 'பள்ளி சேர்க்கை, கல்வி உதவித்தொகை மற்றும் அரசு பணிகளுக்கு மிக முக்கிய ஆவணம்.',
          sub_en: 'Essential proof for education reservations, scholarships, and government job quotas.',
          badge: 'வாழ்நாள் செல்லுபடி',
          points_ta: [
            'BC, MBC, SC, ST பிரிவினரின் இடஒதுக்கீடு உரிமைகளுக்கு கட்டாயம் தேவை',
            'ஒரு முறை பெற்றால் வாழ்நாள் முழுவதும் மீண்டும் புதுப்பிக்க தேவையில்லை',
            'ஆன்லைனில் e-Sevai மூலம் வீட்டிலிருந்தே விண்ணப்பிக்கலாம்'
          ],
          points_en: [
            'Mandatory for all reservation quotas in admissions & public employment',
            'Once issued, it holds permanent lifetime validity across Tamil Nadu',
            'Fully digital online issuance with verifiable QR code'
          ],
          fee: 'அரசு கட்டணம்: ₹60',
          timeline: 'கிடைக்கும் காலம்: 7-15 நாட்கள்'
        },
        {
          heading_ta: 'தேவையான முக்கிய ஆவணங்கள்',
          heading_en: 'Documents Required for Community Certificate',
          sub_ta: 'விண்ணப்பிக்கும் முன் இவற்றை தயாராக வைத்துக் கொள்ளுங்கள்:',
          sub_en: 'Ensure you have clear scanned copies of these documents:',
          badge: 'ஆவணங்கள்',
          points_ta: [
            '1. விண்ணப்பதாரரின் ஆதார் அட்டை & பாஸ்போர்ட் அளவு புகைப்படம்',
            '2. தந்தை அல்லது தாயின் சாதிச் சான்றிதழ் (முக்கிய ஆதாரம்)',
            '3. பள்ளி மாற்றுச் சான்றிதழ் (TC) - சாதி குறிப்பிடப்பட்டிருக்க வேண்டும்',
            '4. குடும்ப அட்டை (Smart Ration Card)'
          ],
          points_en: [
            '1. Applicant Aadhaar card & recent passport photo',
            '2. Father or Mother Community Certificate (Primary evidence)',
            '3. Applicant Transfer Certificate (TC) mentioning caste',
            '4. Family Smart Ration Card'
          ],
          fee: 'அரசு கட்டணம்: ₹60',
          timeline: 'கிடைக்கும் காலம்: 7-15 நாட்கள்'
        }
      ]
    },
    {
      id: 'income_cert',
      title_ta: 'வருமானச் சான்று',
      title_en: 'Income Cert',
      category: 'வருவாய்',
      icon: <Receipt size={22} color="white" />,
      color: 'linear-gradient(135deg, #10b981, #059669)',
      serviceId: 'income_certificate',
      slides: [
        {
          heading_ta: 'வருமானச் சான்றிதழ் — உதவித்தொகைக்கு மிக முக்கியம்',
          heading_en: 'Income Certificate — Key for Welfare & Grants',
          sub_ta: 'அனைத்து கல்வி உதவித்தொகைகள் மற்றும் அரசு நலத்திட்டங்களுக்கு வருமான வரம்பு நிர்ணயிக்கப்படுகிறது.',
          sub_en: 'Determines financial eligibility for fee waivers, scholarships, and subsidized welfare schemes.',
          badge: '1 ஆண்டு செல்லுபடி',
          points_ta: [
            'சான்றிதழ் வழங்கப்பட்ட தேதியிலிருந்து 1 வருடம் வரை மட்டுமே செல்லும்',
            'குடும்பத்தின் அனைத்து உறுப்பினர்களின் மொத்த வருமானமும் கணக்கிடப்படும்',
            'போஸ்ட் மெட்ரிக் உதவித்தொகைக்கு ஆண்டு வருமானம் ₹2.5 லட்சத்திற்குள் இருக்க வேண்டும்'
          ],
          points_en: [
            'Valid strictly for 1 financial year from issuance date',
            'Calculated based on cumulative family income from all sources',
            'Post-matric scholarship ceiling is typically ₹2,50,000 per annum'
          ],
          fee: 'அரசு கட்டணம்: ₹60',
          timeline: 'கிடைக்கும் காலம்: 7-10 நாட்கள்'
        },
        {
          heading_ta: 'வருமானச் சான்றுக்கு என்ன ஆவணங்கள் தேவை?',
          heading_en: 'Required Income Proof Documents',
          sub_ta: 'எளிய ஆவணங்களுடன் உடனடியாக விண்ணப்பிக்கலாம்:',
          sub_en: 'Quick documentation check before online application:',
          badge: 'ஆவணங்கள்',
          points_ta: [
            '1. மாத சம்பளச் சீட்டு (Salary Slip) அல்லது சுயதொழில் வருமான உறுதிமொழி',
            '2. குடும்ப அட்டை (Smart Ration Card)',
            '3. ஆதார் அட்டை & பாஸ்போர்ட் புகைப்படம்',
            '4. வாடகை ஒப்பந்தம் / நில உரிமை விவரம் (இருப்பின்)'
          ],
          points_en: [
            '1. Salary slip / Employer Certificate / Self-declaration of income',
            '2. Smart Ration Card copy',
            '3. Aadhaar Card & passport photo',
            '4. Property tax receipt / Land document (if applicable)'
          ],
          fee: 'அரசு கட்டணம்: ₹60',
          timeline: 'கிடைக்கும் காலம்: 7-10 நாட்கள்'
        }
      ]
    },
    {
      id: 'ration_card',
      title_ta: 'ஸ்மார்ட் ரேஷன்',
      title_en: 'Smart Ration',
      category: 'உணவு & நுகர்வோர்',
      icon: <ShoppingBag size={22} color="white" />,
      color: 'linear-gradient(135deg, #ec4899, #be185d)',
      serviceId: 'smart_ration_card',
      slides: [
        {
          heading_ta: 'TNPDS ஸ்மார்ட் குடும்ப அட்டை',
          heading_en: 'TNPDS Smart Family Ration Card',
          sub_ta: 'புதிய அட்டை விண்ணப்பம், பெயர் சேர்த்தல் அல்லது முகவரி மாற்றம் அனைத்தும் ஆன்லைனில் செய்யலாம்.',
          sub_en: 'Apply for a new smart card, add family members, or modify residential address online.',
          badge: 'TNPDS போர்டல்',
          points_ta: [
            'மளிகைப் பொருட்கள் & நியாயவிலைக் கடை சலுகைகளுக்கு இன்றியமையாதது',
            'மகளிர் உரிமைத் தொகை ₹1000 பெற ரேஷன் அட்டை அடிப்படை ஆவணம்',
            'மாநிலம் முழுவதும் எங்கும் ரேஷன் பொருட்கள் வாங்கும் ஒன் நேஷன் ஒன் ரேஷன் வசதி'
          ],
          points_en: [
            'Essential for PDS subsidized grocery entitlements and commodities',
            'Crucial prerequisite document for Magalir Urimai Thogai (₹1000/mo)',
            'One Nation One Ration Card interoperability across all TN ration shops'
          ],
          fee: 'அரசு கட்டணம்: இலவசம் (₹0)',
          timeline: 'கிடைக்கும் காலம்: 15-30 நாட்கள்'
        }
      ]
    },
    {
      id: 'scholarship_bc_sc',
      title_ta: 'கல்வி உதவித்தொகை',
      title_en: 'Scholarships',
      category: 'மாணவர்',
      icon: <BookOpen size={22} color="white" />,
      color: 'linear-gradient(135deg, #8b5cf6, #6d28d9)',
      serviceId: 'post_matric_scholarship',
      slides: [
        {
          heading_ta: 'தமிழ்நாடு போஸ்ட் மெட்ரிக் ஸ்காலர்ஷிப்',
          heading_en: 'Post-Matric Scholarship Scheme',
          sub_ta: '11th, 12th மற்றும் கல்லூரி மாணவர்களுக்கு கல்விக் கட்டணம் & விடுதிக் கட்டண உதவித்தொகை.',
          sub_en: 'Full tuition reimbursement and hostel allowance for 11th, 12th & Degree students.',
          badge: 'நேரடி வங்கிப் பரிமாற்றம்',
          points_ta: [
            'BC, MBC, SC, ST மாணவர்களுக்கு அரசின் நேரடி நிதியுதவி (DBT)',
            'ஆண்டு வருமான வரம்பு: SC/ST மாணவர்களுக்கு ₹2.5 லட்சம் வரை',
            'வங்கி கணக்குடன் ஆதார் இணைக்கப்பட்டிருக்க வேண்டும் (Aadhaar Seeding)'
          ],
          points_en: [
            'Direct Benefit Transfer (DBT) into student Aadhaar-seeded bank account',
            'Annual income ceiling: Up to ₹2.5 Lakhs for eligible categories',
            'Covers maintenance allowance and mandatory university/college fees'
          ],
          fee: 'அரசு கட்டணம்: இலவசம் (₹0)',
          timeline: 'கிடைக்கும் காலம்: கல்வி ஆண்டு தோறும்'
        }
      ]
    },
    {
      id: 'magalir_urimai',
      title_ta: 'மகளிர் உரிமை',
      title_en: 'Magalir Urimai',
      category: 'நலத்திட்டம்',
      icon: <Heart size={22} color="white" />,
      color: 'linear-gradient(135deg, #f43f5e, #e11d48)',
      serviceId: 'magalir_urimai_thogai',
      slides: [
        {
          heading_ta: 'கலைஞர் மகளிர் உரிமைத் திட்டம் — மாதம் ₹1000',
          heading_en: 'Kalaignar Magalir Urimai Thogai — ₹1000 / Month',
          sub_ta: 'தமிழ்நாட்டின் பெண்களின் பொருளாதார சுதந்திரத்திற்கான அரசின் மாதாந்திர உரிமைத் தொகை.',
          sub_en: 'Monthly financial assistance directly credited to woman family head accounts.',
          badge: 'மாதம் ₹1000',
          points_ta: [
            'குடும்பத் தலைவியின் ஆதார் இணைக்கப்பட்ட வங்கிக் கணக்கில் நேரடியாக வரவு வைக்கப்படும்',
            'ஆண்டு வருமானம் ₹2.5 லட்சத்திற்குள் உள்ள குடும்பங்கள் தகுதியானவர்கள்',
            'விண்ணப்ப நிலை மற்றும் மறுஆய்வை நம்ம சேவை AI மூலம் அறியலாம்'
          ],
          points_en: [
            'Direct credit into the Aadhaar-linked bank account of female head of house',
            'Annual family income ceiling of ₹2.5 Lakhs & electricity consumption norms',
            'Check appeal status, grievance redressal, and bank seeding via AI'
          ],
          fee: 'அரசு கட்டணம்: இலவசம் (₹0)',
          timeline: 'மாதந்தோறும் 15-ம் தேதி வரவு'
        }
      ]
    },
    {
      id: 'uzhavar_card',
      title_ta: 'உழவர் நலன்',
      title_en: 'Farmer Welfare',
      category: 'விவசாயம்',
      icon: <Sprout size={22} color="white" />,
      color: 'linear-gradient(135deg, #10b981, #047857)',
      serviceId: 'farmer_registration',
      slides: [
        {
          heading_ta: 'உழவர் பாதுகாப்பு அட்டை & மானியங்கள்',
          heading_en: 'Uzhavar Welfare & Agricultural Subsidies',
          sub_ta: 'பயிர் காப்பீடு, உழவர் பாதுகாப்புத் திட்டம் மற்றும் வேளாண் இயந்திர மானியங்கள்.',
          sub_en: 'Crop insurance claim support, farmer safety net, and machinery subsidies.',
          badge: 'விவசாயி உதவி',
          points_ta: [
            'விவசாயிகள் மற்றும் விவசாயத் தொழிலாளர்களுக்கு முழு பாதுகாப்பு திட்டம்',
            'இயற்கை சீற்றங்களின் போது பயிர் இழப்பீட்டு உதவித்தொகை',
            'உழவர் பாதுகாப்பு அட்டையுடன் எளிய மருத்துவ & ஓய்வூதிய பலன்கள்'
          ],
          points_en: [
            'Comprehensive safety scheme for farmers and agricultural laborers',
            'Direct crop loss compensation payouts during monsoon & disaster damages',
            'Uzhavar identity card for hassle-free farmer pension and health benefits'
          ],
          fee: 'அரசு கட்டணம்: இலவசம் (₹0)',
          timeline: 'கிடைக்கும் காலம்: 7-15 நாட்கள்'
        }
      ]
    }
  ];

  const handleOpenStory = (story: Story) => {
    setActiveStory(story);
    setCurrentSlideIndex(0);
    setProgress(0);
  };

  const handleCloseStory = () => {
    setActiveStory(null);
    setCurrentSlideIndex(0);
    setProgress(0);
  };

  const handleNextSlide = () => {
    if (!activeStory) return;
    if (currentSlideIndex < activeStory.slides.length - 1) {
      setCurrentSlideIndex((prev) => prev + 1);
      setProgress(0);
    } else {
      handleCloseStory();
    }
  };

  const handlePrevSlide = () => {
    if (!activeStory) return;
    if (currentSlideIndex > 0) {
      setCurrentSlideIndex((prev) => prev - 1);
      setProgress(0);
    }
  };

  // Auto-progress slides like Instagram
  useEffect(() => {
    if (!activeStory) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          handleNextSlide();
          return 0;
        }
        return prev + 2;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [activeStory, currentSlideIndex]);

  const currentSlide = activeStory ? activeStory.slides[currentSlideIndex] : null;

  return (
    <div className="instagram-stories-wrapper">
      <div className="stories-header">
        <div className="stories-title">
          <Sparkles size={16} className="text-amber-500 animate-spin-slow" />
          <span>{language === 'ta' ? 'விரைவு 1-நிமிட வழிகாட்டிகள் (Reels & Guides)' : '1-Minute Visual Guides (Quick Stories)'}</span>
        </div>
        <span className="stories-hint">
          {language === 'ta' ? 'தொட்டுப் பார்க்கவும்' : 'Tap to View'}
        </span>
      </div>

      <div className="stories-carousel">
        {stories.map((story) => (
          <button
            key={story.id}
            className="story-item"
            onClick={() => handleOpenStory(story)}
            title={language === 'ta' ? story.title_ta : story.title_en}
          >
            <div className="story-ring">
              <div className="story-avatar" style={{ background: story.color }}>
                <span className="story-emoji">{story.icon}</span>
              </div>
            </div>
            <span className="story-name">
              {language === 'ta' ? story.title_ta : story.title_en}
            </span>
          </button>
        ))}
      </div>

      {/* Fullscreen Instagram / WhatsApp Status Modal */}
      {activeStory && currentSlide && (
        <div className="story-modal-backdrop" onClick={handleCloseStory}>
          <div className="story-modal-card" onClick={(e) => e.stopPropagation()}>
            {/* Story Top Progress Bars */}
            <div className="story-progress-container">
              {activeStory.slides.map((_, idx) => (
                <div key={idx} className="story-progress-track">
                  <div
                    className="story-progress-fill"
                    style={{
                      width:
                        idx < currentSlideIndex
                          ? '100%'
                          : idx === currentSlideIndex
                          ? `${progress}%`
                          : '0%'
                    }}
                  />
                </div>
              ))}
            </div>

            {/* Story Modal Header */}
            <div className="story-modal-header">
              <div className="story-user-info">
                <div className="story-mini-avatar" style={{ background: activeStory.color }}>
                  {activeStory.icon}
                </div>
                <div>
                  <div className="story-modal-title">
                    {language === 'ta' ? activeStory.title_ta : activeStory.title_en}
                  </div>
                  <div className="story-modal-subtitle">
                    {language === 'ta' ? 'அதிகாரப்பூர்வ தமிழ்நாடு அரசு வழிகாட்டி' : 'TN Verified Civic Guide'}
                  </div>
                </div>
              </div>
              <button className="story-close-btn" onClick={handleCloseStory}>
                <X size={20} />
              </button>
            </div>

            {/* Story Content Slide */}
            <div className="story-body">
              <div className="story-slide-badge">
                <ShieldCheck size={14} />
                <span>{currentSlide.badge}</span>
              </div>

              <h3 className="story-slide-heading">
                {language === 'ta' ? currentSlide.heading_ta : currentSlide.heading_en}
              </h3>

              <p className="story-slide-sub">
                {language === 'ta' ? currentSlide.sub_ta : currentSlide.sub_en}
              </p>

              <div className="story-points-card">
                {(language === 'ta' ? currentSlide.points_ta : currentSlide.points_en).map((pt, i) => (
                  <div key={i} className="story-point-row">
                    <CheckCircle2 size={16} className="text-emerald-500 flex-shrink-0" />
                    <span>{pt}</span>
                  </div>
                ))}
              </div>

              {/* Meta stats bar */}
              <div className="story-meta-bar">
                <div className="story-meta-item">
                  <Clock size={14} />
                  <span>{currentSlide.timeline}</span>
                </div>
                <div className="story-meta-item">
                  <FileText size={14} />
                  <span>{currentSlide.fee}</span>
                </div>
              </div>
            </div>

            {/* Story Bottom CTA */}
            <div className="story-footer">
              <button
                className="story-action-btn"
                onClick={() => {
                  handleCloseStory();
                  onSelectStoryService(activeStory.serviceId);
                }}
              >
                <span>{language === 'ta' ? 'இப்போதே விண்ணப்பிக்க வழிகாட்டி' : 'Start Application Guide'}</span>
                <ArrowRight size={18} />
              </button>
            </div>

            {/* Left / Right Tap Click Targets */}
            <button className="story-nav-btn prev" onClick={handlePrevSlide} disabled={currentSlideIndex === 0}>
              <ChevronLeft size={24} />
            </button>
            <button className="story-nav-btn next" onClick={handleNextSlide}>
              <ChevronRight size={24} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

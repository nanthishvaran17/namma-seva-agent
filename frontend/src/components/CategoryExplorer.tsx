import React, { useState } from 'react';
import { 
  Award, GraduationCap, Users, Sprout, ShoppingBag, 
  HeartHandshake, Check, ArrowRight, Clock, FileText, 
  Sparkles, PhoneCall, ChevronRight, X, ShieldCheck, Share2,
  HelpCircle, CheckCircle2, AlertCircle, RefreshCw
} from 'lucide-react';

interface CategoryExplorerProps {
  language: string;
  onSelectCategory: (catId: string) => void;
  onStartService?: (serviceId: string) => void;
  onAskServiceAI?: (query: string) => void;
}

interface QuickService {
  id: string;
  title_ta: string;
  title_en: string;
  category: string;
  icon: string;
  bg: string;
  fee_ta: string;
  fee_en: string;
  days_ta: string;
  days_en: string;
  badge_ta?: string;
  desc_ta: string;
  desc_en: string;
  docs_ta: string[];
  docs_en: string[];
  steps_ta: string[];
  steps_en: string[];
}

export const CategoryExplorer: React.FC<CategoryExplorerProps> = ({
  language,
  onSelectCategory,
  onStartService,
  onAskServiceAI,
}) => {
  const [selectedService, setSelectedService] = useState<QuickService | null>(null);
  const [currentDocIndex, setCurrentDocIndex] = useState(0);
  const [docAnswers, setDocAnswers] = useState<Record<number, boolean>>({});
  const [wizardFinished, setWizardFinished] = useState(false);
  const [showHelpNote, setShowHelpNote] = useState<string | null>(null);

  const alternativeTips: Record<string, { ta: string; en: string }> = {
    community_certificate: {
      ta: 'கவலை வேண்டாம்! பெற்றோரின் சாதிச் சான்றிதழ் இல்லாவிட்டால், தந்தை அல்லது தாயின் பள்ளி மாற்றுச் சான்றிதழ் (TC) அல்லது இரத்த வழி உறவினரின் சான்றிதழை ஆதாரமாகப் பயன்படுத்தலாம்.',
      en: 'No worries! If parents do not have a community cert, their school TC or blood relatives’ certificate can be accepted as valid proof.'
    },
    income_certificate: {
      ta: 'மாத சம்பளச் சீட்டு இல்லாவிட்டால், கிராம நிர்வாக அலுவலரிடம் (VAO) சுய உறுதிமொழிப் படிவம் (Self-Declaration) பெற்று சமர்ப்பிக்கலாம்.',
      en: 'If you do not have a salary slip, self-employed persons can submit a simple Self-Declaration affidavit at the VAO office.'
    },
    first_graduate_certificate: {
      ta: 'பெற்றோர் பள்ளி செல்லவில்லை என்றால், அவர்கள் படிப்பறிவின்மை உறுதிமொழிப் படிவத்தில் (Joint Declaration) கையொப்பமிட்டால் போதுமானது.',
      en: 'If parents did not attend school, signing the official Joint Declaration of illiteracy affidavit is sufficient.'
    },
    post_matric_scholarship: {
      ta: 'வங்கிக் கணக்குடன் ஆதார் இணைக்கப்படவில்லை என்றால் (Aadhaar Seeding), உங்கள் வங்கிக் கிளையை அணுகி 1 நாளில் NPCI மேப்பிங் செய்யலாம்.',
      en: 'If Aadhaar is not seeded to bank account, visit your bank branch to complete NPCI mapping in 1 day.'
    },
    smart_ration_card: {
      ta: 'எரிவாயு இணைப்பு ரசீது இல்லையென்றால், "எரிவாயு இல்லாத குடும்பம் (No LPG)" என தேர்வு செய்து ரேஷன் அட்டைக்கு விண்ணப்பிக்கலாம்.',
      en: 'If you do not have an LPG gas bill, you can select "No LPG Cylinder" and apply for smart card easily.'
    },
    magalir_urimai_thogai: {
      ta: 'சொந்த வீடு அல்லது நில ஆவணங்கள் தேவையில்லை! குடும்ப ரேஷன் அட்டை, ஆதார் மற்றும் மின்சார இணைப்பு எண் மட்டுமே போதுமானது.',
      en: 'No property docs needed! Smart ration card, Aadhaar, and electricity consumer number are sufficient.'
    },
    nativity_certificate: {
      ta: 'பிறப்புச் சான்றிதழ் இல்லாவிட்டால், தமிழ்நாட்டில் 5 ஆண்டுகள் படித்ததற்கான பள்ளி மாற்றுச் சான்றிதழ் (TC) அல்லது ரேஷன் அட்டை போதும்.',
      en: 'If birth certificate is unavailable, 5-year study proof / school TC or family ration card serves as valid residence proof.'
    },
    farmer_registration: {
      ta: 'சொந்த நிலம் இல்லாத குத்தகை விவசாயிகள், கிராம நிர்வாக அலுவலரிடம் உழவர் சாகுபடி உறுதிமொழி பெற்று நலத்திட்டங்களைப் பெறலாம்.',
      en: 'Tenant farmers without land patta can obtain a cultivation certificate from the VAO to register.'
    }
  };

  // PhonePe / Google Pay style visual services
  const quickServices: QuickService[] = [
    {
      id: 'community_certificate',
      title_ta: 'சாதிச் சான்றிதழ்',
      title_en: 'Community Certificate',
      category: 'வருவாய்த் துறை',
      icon: '📜',
      bg: 'linear-gradient(135deg, #0071e3, #42a5f5)',
      fee_ta: '₹60 மட்டும்',
      fee_en: '₹60 Only',
      days_ta: '7–15 நாட்கள்',
      days_en: '7–15 Days',
      badge_ta: 'வாழ்நாள் செல்லுபடி',
      desc_ta: 'பள்ளி, கல்லூரி சேர்க்கை, அரசு வேலைவாய்ப்பு மற்றும் இடஒதுக்கீடு சலுகைகளுக்கு வாழ்நாள் முழுவதும் செல்லும் சான்றிதழ்.',
      desc_en: 'Mandatory certificate for reservations, admissions, and public employment with permanent lifetime validity.',
      docs_ta: [
        'விண்ணப்பதாரர் ஆதார் அட்டை',
        'தந்தை அல்லது தாயின் சாதிச் சான்றிதழ் (முக்கிய ஆதாரம்)',
        'பள்ளி மாற்றுச் சான்றிதழ் (TC)',
        'குடும்ப ஸ்மார்ட் ரேஷன் அட்டை'
      ],
      docs_en: [
        'Applicant Aadhaar Card',
        'Father or Mother Community Certificate',
        'Applicant School TC',
        'Family Smart Ration Card'
      ],
      steps_ta: [
        '1. தேவையான ஆவணங்களை புகைப்படம் எடுத்து வைத்துக் கொள்ளுங்கள்',
        '2. அருகிலுள்ள இ-சேவை மையம் அல்லது tnesevai இணையதளத்தில் விண்ணப்பிக்கவும்',
        '3. VAO மற்றும் RI ஆய்வுக்குப் பின் தாசில்தார் டிஜிட்டல் கையொப்பமிட்ட சான்றிதழ் கிடைக்கும்'
      ],
      steps_en: [
        '1. Keep scanned copies of documents ready',
        '2. Apply via nearest e-Sevai or tnesevai.tn.gov.in portal',
        '3. Receive digitally signed certificate from Tahsildar after verification'
      ]
    },
    {
      id: 'income_certificate',
      title_ta: 'வருமானச் சான்றிதழ்',
      title_en: 'Income Certificate',
      category: 'வருவாய்த் துறை',
      icon: '💰',
      bg: 'linear-gradient(135deg, #34c759, #30b0c7)',
      fee_ta: '₹60 மட்டும்',
      fee_en: '₹60 Only',
      days_ta: '5–10 நாட்கள்',
      days_en: '5–10 Days',
      badge_ta: '1 ஆண்டு செல்லும்',
      desc_ta: 'அனைத்து கல்வி உதவித்தொகைகள், கட்டண சலுகைகள் மற்றும் அரசு நலத்திட்டங்களுக்கு மிக அவசியமான சான்றிதழ்.',
      desc_en: 'Essential annual proof of family income for scholarships, fee waivers, and state subsidies.',
      docs_ta: [
        'குடும்ப ஸ்மார்ட் ரேஷன் அட்டை',
        'மாத சம்பளச் சீட்டு அல்லது சுயதொழில் வருமான உறுதிமொழி',
        'விண்ணப்பதாரர் ஆதார் அட்டை',
        'பாஸ்போர்ட் அளவு புகைப்படம்'
      ],
      docs_en: [
        'Smart Ration Card copy',
        'Salary slip or Self-Declaration of income',
        'Applicant Aadhaar Card',
        'Recent passport size photo'
      ],
      steps_ta: [
        '1. குடும்பத்தின் மொத்த ஆண்டு வருமான விவரங்களை உறுதிப்படுத்தவும்',
        '2. இ-சேவை போர்ட்டலில் ஆவணங்களைப் பதிவேற்றி சமர்ப்பிக்கவும்',
        '3. கிராம நிர்வாக அலுவலர் (VAO) சரிபார்த்த பின் சான்றிதழ் பதிவிறக்கம் செய்யலாம்'
      ],
      steps_en: [
        '1. Confirm cumulative family annual income details',
        '2. Upload documents on official e-Sevai portal',
        '3. Download verified certificate after VAO review'
      ]
    },
    {
      id: 'first_graduate_certificate',
      title_ta: 'முதல் பட்டதாரி',
      title_en: 'First Graduate',
      category: 'உயர் கல்வித் துறை',
      icon: '🎓',
      bg: 'linear-gradient(135deg, #ff9500, #ffb74d)',
      fee_ta: '₹60 மட்டும்',
      fee_en: '₹60 Only',
      days_ta: '7–15 நாட்கள்',
      days_en: '7–15 Days',
      badge_ta: 'ஆண்டுக்கு ₹25,000 சலுகை',
      desc_ta: 'குடும்பத்தின் முதல் பட்டதாரி மாணவருக்கு அண்ணா பல்கலைக்கழகம் & அரசு கவுன்சிலிங் கல்லூரிகளில் ஆண்டுதோறும் கட்டணக் குறைப்பு.',
      desc_en: 'Direct tuition fee waiver of up to ₹25,000 per academic year for first-generation graduates across TN colleges.',
      docs_ta: [
        'மாணவரின் 10th / 12th மதிப்பெண் சான்றிதழ்',
        'பெற்றோரின் பள்ளி மாற்றுச் சான்றிதழ் (TC) அல்லது படிப்பறிவின்மை உறுதிமொழி',
        'உடன்பிறப்புகளின் பள்ளி/கல்லூரி மாற்றுச் சான்றிதழ் (TC)',
        'குடும்ப ஸ்மார்ட் ரேஷன் அட்டை & ஆதார் அட்டை'
      ],
      docs_en: [
        'Student 10th & 12th Marksheets',
        'Parents School TC or Joint Declaration',
        'Siblings Educational Proof / TC',
        'Smart Ration Card & Aadhaar'
      ],
      steps_ta: [
        '1. குடும்பத்தில் பெற்றோர், உடன்பிறப்புகள் யாரும் பட்டம் பெறவில்லை என்பதை உறுதிப்படுத்தவும்',
        '2. கூட்டறிக்கை (Joint Declaration) படிவத்தில் கையொப்பமிடவும்',
        '3. இ-சேவை மூலம் விண்ணப்பித்து கல்லூரி சேர்க்கையில் கட்டண விலக்கு பெறவும்'
      ],
      steps_en: [
        '1. Verify no parents or siblings hold a degree',
        '2. Sign the official Joint Declaration affidavit',
        '3. Apply via e-Sevai and submit certificate during college admission'
      ]
    },
    {
      id: 'post_matric_scholarship',
      title_ta: 'கல்வி உதவித்தொகை',
      title_en: 'Scholarship',
      category: 'மாணவர் நலன்',
      icon: '💵',
      bg: 'linear-gradient(135deg, #af52de, #5856d6)',
      fee_ta: 'இலவசம் (₹0)',
      fee_en: 'Free (₹0)',
      days_ta: 'கல்வி ஆண்டு',
      days_en: 'Academic Cycle',
      badge_ta: 'வங்கி கணக்கில் வரவு',
      desc_ta: '11th, 12th மற்றும் கல்லூரி மாணவர்களுக்கு கல்விக் கட்டணம் & விடுதிக் கட்டணத்திற்கான அரசின் நேரடி உதவித்தொகை.',
      desc_en: 'Full tuition fee reimbursement and maintenance allowance directly credited into student bank account.',
      docs_ta: [
        'சாதிச் சான்றிதழ் (BC/MBC/SC/ST)',
        'வருமானச் சான்றிதழ் (ஆண்டு வருமானம் ரூ.2.5L-க்குள்)',
        'மாணவரின் ஆதார் இணைக்கப்பட்ட வங்கிக் கணக்கு பாஸ்புக்',
        'கல்லூரி கட்டண ரசீது & Bonafide சான்றிதழ்'
      ],
      docs_en: [
        'Community Certificate',
        'Income Certificate (< ₹2.5 Lakhs)',
        'Aadhaar-Seeded Bank Passbook',
        'College Fee Receipt & Bonafide Certificate'
      ],
      steps_ta: [
        '1. வங்கிக் கணக்குடன் ஆதார் இணைக்கப்பட்டுள்ளதா (Aadhaar Seeding) என சரிபார்க்கவும்',
        '2. கல்லூரி மூலமாகவோ அல்லது UMANG போர்ட்டல் வழியாகவோ விண்ணப்பிக்கவும்',
        '3. அரசின் உதவித்தொகை நேரடியாக வங்கிக் கணக்கில் வந்து சேரும்'
      ],
      steps_en: [
        '1. Ensure bank account is active with Aadhaar seeding',
        '2. Apply through college nodal desk or scholarship portal',
        '3. Financial allowance credited directly via DBT'
      ]
    },
    {
      id: 'smart_ration_card',
      title_ta: 'ஸ்மார்ட் ரேஷன்',
      title_en: 'Smart Ration',
      category: 'TNPDS உணவுத் துறை',
      icon: '🍚',
      bg: 'linear-gradient(135deg, #ff2d55, #ff375f)',
      fee_ta: 'இலவசம் (₹0)',
      fee_en: 'Free (₹0)',
      days_ta: '15–30 நாட்கள்',
      days_en: '15–30 Days',
      badge_ta: 'மானிய மளிகை',
      desc_ta: 'புதிய ஸ்மார்ட் குடும்ப அட்டை, புதிய உறுப்பினர் சேர்த்தல், குடும்பத் தலைவி மாற்றம் மற்றும் முகவரி திருத்தம்.',
      desc_en: 'Apply for new family smart ration card, add or remove members, change head of family or address.',
      docs_ta: [
        'குடும்பத்தின் அனைத்து உறுப்பினர்களின் ஆதார் அட்டை',
        'சமையல் எரிவாயு இணைப்பு ரசீது (LPG Bill)',
        'வாடகை ஒப்பந்தம் அல்லது மின்சார ரசீது (முகவரி ஆதாரம்)',
        'குடும்பத் தலைவியின் பாஸ்போர்ட் புகைப்படம்'
      ],
      docs_en: [
        'Aadhaar cards of all family members',
        'LPG Gas connection receipt',
        'Electricity bill or Rental Agreement',
        'Passport photo of female family head'
      ],
      steps_ta: [
        '1. உறுப்பினர்கள் ஆதார் எண்களை தயாராக வைத்துக் கொள்ளவும்',
        '2. tnpds.gov.in இணையதளத்தில் புதிய அட்டைக்கு விண்ணப்பிக்கவும்',
        '3. தாலுகா வழங்கல் அலுவலர் (TSO) ஒப்புதலுக்குப் பின் அட்டை வீட்டிற்கு வரும்'
      ],
      steps_en: [
        '1. Keep all Aadhaar details verified',
        '2. Apply online at tnpds.gov.in portal',
        '3. Smart card printed and dispatched after TSO inspection'
      ]
    },
    {
      id: 'magalir_urimai_thogai',
      title_ta: 'மகளிர் உரிமை',
      title_en: 'Magalir Urimai',
      category: 'சமூக நலத்துறை',
      icon: '👩‍💼',
      bg: 'linear-gradient(135deg, #ff3b30, #ff6482)',
      fee_ta: 'இலவசம் (₹0)',
      fee_en: 'Free (₹0)',
      days_ta: 'மாதம் 15-ம் தேதி',
      days_en: 'Every 15th',
      badge_ta: 'மாதம் ₹1,000',
      desc_ta: 'குடும்பத் தலைவிகளின் பொருளாதார முன்னேற்றத்திற்காக தமிழ்நாடு அரசின் மாதாந்திர ₹1,000 நேரடி வங்கி உதவித்தொகை.',
      desc_en: 'Direct monthly financial support of ₹1,000 credited to female heads of eligible households.',
      docs_ta: [
        'ஸ்மார்ட் குடும்ப அட்டை (Ration Card)',
        'குடும்பத் தலைவியின் ஆதார் அட்டை',
        'ஆதார் இணைக்கப்பட்ட வங்கிக் கணக்கு',
        'மின்சார கட்டண இணைப்பு எண்'
      ],
      docs_en: [
        'Smart Family Ration Card',
        'Aadhaar card of female head of house',
        'Aadhaar-seeded bank account',
        'Electricity service connection number'
      ],
      steps_ta: [
        '1. குடும்ப ஆண்டு வருமானம் ₹2.5 லட்சத்திற்குள் இருப்பதை உறுதிசெய்யவும்',
        '2. இ-சேவை மையம் அல்லது சிறப்பு முகாம்களில் பதிவு செய்யவும்',
        '3. ஒப்புதலுக்குப் பின் ஒவ்வொரு மாதமும் 15-ம் தேதி ₹1,000 கணக்கில் வரும்'
      ],
      steps_en: [
        '1. Verify annual income criteria (< ₹2.5 Lakhs)',
        '2. Register at e-Sevai or designated camps',
        '3. ₹1,000 deposited directly on the 15th of every month'
      ]
    },
    {
      id: 'nativity_certificate',
      title_ta: 'இருப்பிடச் சான்று',
      title_en: 'Nativity Cert',
      category: 'வருவாய்த் துறை',
      icon: '🏠',
      bg: 'linear-gradient(135deg, #0071e3, #5856d6)',
      fee_ta: '₹60 மட்டும்',
      fee_en: '₹60 Only',
      days_ta: '7–10 நாட்கள்',
      days_en: '7–10 Days',
      badge_ta: 'கவுன்சிலிங் இட ஒதுக்கீடு',
      desc_ta: 'தமிழ்நாட்டில் தொடர்ந்து 5 ஆண்டுகள் வசித்து வருவதற்கான சான்று. மருத்துவம் மற்றும் பொறியியல் கவுன்சிலிங்கிற்கு கட்டாயம்.',
      desc_en: 'Continuous 5-year residency proof required for Tamil Nadu state quota in MBBS, BDS, and Engineering.',
      docs_ta: [
        'கடந்த 5 ஆண்டுகளுக்கான இருப்பிடச் சான்றுகள் (ரேஷன் அட்டை, வாடகை ஒப்பந்தம்)',
        'பள்ளி மாற்றுச் சான்றிதழ் (TC) - தமிழ்நாட்டில் படித்ததற்கான ஆதாரம்',
        'விண்ணப்பதாரர் மற்றும் பெற்றோர் ஆதார் அட்டை'
      ],
      docs_en: [
        '5-Year continuous residency proofs (Ration card, rent deeds)',
        'School Transfer Certificate showing study in TN',
        'Applicant and Parent Aadhaar Cards'
      ],
      steps_ta: [
        '1. தமிழ்நாட்டில் 5 ஆண்டுகள் வசித்த ஆவணங்களை ஒருங்கிணைக்கவும்',
        '2. இ-சேவை மூலம் CAN எண் பதிவு செய்து விண்ணப்பிக்கவும்',
        '3. தாசில்தார் கையொப்பமிட்ட சான்றிதழைப் பதிவிறக்கம் செய்யவும்'
      ],
      steps_en: [
        '1. Gather continuous 5-year residence evidence',
        '2. Submit online application with CAN registration',
        '3. Download verified certificate after approval'
      ]
    },
    {
      id: 'farmer_registration',
      title_ta: 'உழவர் நலன்',
      title_en: 'Farmer Welfare',
      category: 'வேளாண்மைத் துறை',
      icon: '🌾',
      bg: 'linear-gradient(135deg, #34c759, #30d158)',
      fee_ta: 'இலவசம் (₹0)',
      fee_en: 'Free (₹0)',
      days_ta: '7–15 நாட்கள்',
      days_en: '7–15 Days',
      badge_ta: 'பயிர் காப்பீடு & மானியம்',
      desc_ta: 'விவசாயிகள் மற்றும் விவசாய தொழிலாளர்களுக்கு இயற்கை பேரிடர் இழப்பீடு, பயிர் காப்பீடு மற்றும் அரசு மானியங்கள்.',
      desc_en: 'Crop insurance claims, disaster compensation, seed subsidies, and social safety net for agricultural families.',
      docs_ta: [
        'நில பட்டா / சிட்டா நகல்',
        'விவசாயி ஆதார் அட்டை',
        'வங்கி கணக்கு பாஸ்புக் நகல்',
        'குடும்ப ஸ்மார்ட் ரேஷன் அட்டை'
      ],
      docs_en: [
        'Land Patta / Chitta document',
        'Farmer Aadhaar Card',
        'Bank account passbook copy',
        'Smart Ration Card'
      ],
      steps_ta: [
        '1. நில விவரங்கள் (சர்வே எண், பட்டா) தயாராக வைக்கவும்',
        '2. உழவன் செயலி (Uzhavan App) அல்லது வேளாண் அலுவலகத்தில் பதியவும்',
        '3. நேரடி மானியம் மற்றும் பயிர் காப்பீட்டு பலன்களைப் பெறவும்'
      ],
      steps_en: [
        '1. Keep land survey and patta details ready',
        '2. Register via Uzhavan App or Agriculture Dept desk',
        '3. Access direct crop subsidies and claim benefits'
      ]
    }
  ];

  return (
    <section className="phonepe-container">
      {/* 1. Big Visual Tiles Section — Like PhonePe / Google Pay */}
      <div className="phonepe-card-wrapper">
        <div className="phonepe-section-top">
          <div>
            <h2 className="phonepe-main-title">
              {language === 'ta' ? 'அரசு சேவைகள் — விரைவுத் தேர்வுகள்' : 'Popular Government Services'}
            </h2>
            <p className="phonepe-sub-title">
              {language === 'ta' ? 'உங்களுக்குத் தேவையான சான்றிதழைத் தொடவும் (1-கிளிக் வழிகாட்டி):' : 'Tap any service to view required documents and apply:'}
            </p>
          </div>
          <button 
            className="phonepe-view-all-pill"
            onClick={() => onSelectCategory('all')}
          >
            <span>{language === 'ta' ? 'அனைத்து சேவைகள்' : 'View All'}</span>
            <ChevronRight size={16} />
          </button>
        </div>

        {/* 8 Big Touch-Friendly Visual Tiles */}
        <div className="phonepe-grid">
          {quickServices.map((svc) => (
            <button
              key={svc.id}
              type="button"
              className="phonepe-tile-btn"
              onClick={() => {
                setSelectedService(svc);
                setCurrentDocIndex(0);
                setDocAnswers({});
                setWizardFinished(false);
                setShowHelpNote(null);
              }}
            >
              <div className="phonepe-tile-icon-box" style={{ background: svc.bg }}>
                <span className="phonepe-emoji">{svc.icon}</span>
              </div>
              <span className="phonepe-tile-name">
                {language === 'ta' ? svc.title_ta : svc.title_en}
              </span>
              <div className="phonepe-tile-meta-row">
                <span className="phonepe-tile-tag">
                  {language === 'ta' ? svc.fee_ta : svc.fee_en}
                </span>
                {svc.badge_ta && (
                  <span className="phonepe-tile-badge-sub">
                    {language === 'ta' ? svc.badge_ta : svc.title_en}
                  </span>
                )}
              </div>
              <span className="phonepe-tile-action-prompt">
                {language === 'ta' ? '👉 தொட்டுச் சரிபார்க்கவும்' : '👉 Tap to Check'}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 2. Quick Helpline & Verified Source Banner */}
      <div className="phonepe-banner-row">
        <div className="phonepe-banner-item helpline">
          <div className="banner-icon-circle green">
            <PhoneCall size={20} color="#34c759" />
          </div>
          <div>
            <div className="banner-bold-title">
              {language === 'ta' ? 'முதல்வர் உதவி எண்: 1100' : 'CM Helpline: 1100'}
            </div>
            <div className="banner-desc">
              {language === 'ta' ? '24 மணி நேரமும் இலவச உதவி மற்றும் குறைகள் பதிவு' : '24x7 Free civic guidance and grievance registration'}
            </div>
          </div>
        </div>

        <div className="phonepe-banner-item official">
          <div className="banner-icon-circle blue">
            <ShieldCheck size={20} color="#0071e3" />
          </div>
          <div>
            <div className="banner-bold-title">
              {language === 'ta' ? '100% அதிகாரப்பூர்வ தகவல்கள்' : '100% Official & Verified'}
            </div>
            <div className="banner-desc">
              {language === 'ta' ? 'தமிழ்நாடு அரசு குடிமக்கள் சாசனம் (tnesevai.tn.gov.in)' : 'Ground-verified with TN Government Citizen Charters'}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Step-by-Step Interactive Guided Wizard Modal */}
      {selectedService && (() => {
        const docs = language === 'ta' ? selectedService.docs_ta : selectedService.docs_en;
        const totalDocs = docs.length;
        const currentDoc = docs[currentDocIndex];

        return (
          <div className="phonepe-modal-backdrop" onClick={() => setSelectedService(null)}>
            <div className="phonepe-modal-sheet" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="phonepe-modal-header">
                <div className="phonepe-modal-title-group">
                  <div className="phonepe-modal-icon-badge" style={{ background: selectedService.bg }}>
                    {selectedService.icon}
                  </div>
                  <div>
                    <h3 className="phonepe-modal-heading">
                      {language === 'ta' ? selectedService.title_ta : selectedService.title_en}
                    </h3>
                    <span className="phonepe-modal-sub">
                      {selectedService.category} • {language === 'ta' ? selectedService.fee_ta : selectedService.fee_en} • {language === 'ta' ? selectedService.days_ta : selectedService.days_en}
                    </span>
                  </div>
                </div>

                <button className="phonepe-close-btn" onClick={() => setSelectedService(null)}>
                  <X size={20} />
                </button>
              </div>

              {/* Wizard Content: Step by Step */}
              {!wizardFinished ? (
                <div>
                  {/* Progress Header */}
                  <div className="wizard-progress-section">
                    <div className="wizard-progress-info">
                      <span>{language === 'ta' ? 'படி படியான ஆவண சரிபார்ப்பு' : 'Step-by-Step Document Check'}</span>
                      <span className="wizard-step-pill">
                        {language === 'ta' ? `ஆவணம் ${currentDocIndex + 1} / ${totalDocs}` : `Document ${currentDocIndex + 1} of ${totalDocs}`}
                      </span>
                    </div>
                    <div className="wizard-progress-track">
                      <div 
                        className="wizard-progress-fill" 
                        style={{ width: `${((currentDocIndex + 1) / totalDocs) * 100}%` }} 
                      />
                    </div>
                  </div>

                  {/* Interactive Question Card */}
                  <div className="wizard-question-box">
                    <span className="wizard-q-label">
                      {language === 'ta' ? '❓ உங்களிடம் இந்த ஆவணம் உள்ளதா?' : '❓ Do you have this document ready?'}
                    </span>
                    <div className="wizard-doc-display">
                      <span className="doc-num-circle">{currentDocIndex + 1}</span>
                      <h4 className="wizard-doc-name">{currentDoc}</h4>
                    </div>
                    <p className="wizard-doc-sub">
                      {language === 'ta' 
                        ? 'அரசு இ-சேவை மூலம் விண்ணப்பிக்க இந்த ஆவணம் தேவைப்படுகிறது.' 
                        : 'This document is verified by authorities during submission.'}
                    </p>

                    {/* Choice Buttons */}
                    <div className="wizard-choices-row">
                      <button
                        type="button"
                        className="wizard-choice-btn yes"
                        onClick={() => {
                          setDocAnswers(prev => ({ ...prev, [currentDocIndex]: true }));
                          setShowHelpNote(null);
                          if (currentDocIndex + 1 < totalDocs) {
                            setCurrentDocIndex(prev => prev + 1);
                          } else {
                            setWizardFinished(true);
                          }
                        }}
                      >
                        <CheckCircle2 size={22} color="#15803d" />
                        <span>{language === 'ta' ? 'ஆம், என்னிடம் உள்ளது' : 'Yes, I Have It'}</span>
                      </button>

                      <button
                        type="button"
                        className="wizard-choice-btn no"
                        onClick={() => {
                          setDocAnswers(prev => ({ ...prev, [currentDocIndex]: false }));
                          const tip = alternativeTips[selectedService.id]?.[language === 'ta' ? 'ta' : 'en'] || (
                            language === 'ta'
                              ? 'இந்த ஆவணம் இல்லாவிட்டால் மாற்று ஆவணம் அல்லது VAO உறுதிமொழி மூலம் விண்ணப்பிக்கலாம்.'
                              : 'You may use an alternate proof or Self-Declaration affidavit.'
                          );
                          setShowHelpNote(tip);
                        }}
                      >
                        <HelpCircle size={22} color="#b45309" />
                        <span>{language === 'ta' ? 'இல்லை / மாற்று வழி என்ன?' : 'No / What Alternative?'}</span>
                      </button>
                    </div>

                    {/* Empathetic Helpful Tip when User Clicks "No" */}
                    {showHelpNote && (
                      <div className="wizard-tip-box">
                        <div className="wizard-tip-title">
                          <AlertCircle size={18} color="#b45309" />
                          <span>{language === 'ta' ? '💡 கவலை வேண்டாம்! அரசு மாற்று வழி:' : '💡 Official Alternative Guide:'}</span>
                        </div>
                        <p className="wizard-tip-text">{showHelpNote}</p>
                        <div className="wizard-tip-actions">
                          <button
                            type="button"
                            className="phonepe-primary-btn"
                            style={{ padding: '8px 14px', fontSize: '0.82rem' }}
                            onClick={() => {
                              setShowHelpNote(null);
                              if (currentDocIndex + 1 < totalDocs) {
                                setCurrentDocIndex(prev => prev + 1);
                              } else {
                                setWizardFinished(true);
                              }
                            }}
                          >
                            <span>{language === 'ta' ? 'அடுத்த ஆவணம் பார்க்க ➔' : 'Check Next Document ➔'}</span>
                          </button>

                          <button
                            type="button"
                            className="phonepe-share-btn"
                            style={{ padding: '8px 14px', fontSize: '0.82rem' }}
                            onClick={() => {
                              const q = `${selectedService.title_ta} விண்ணப்பிக்க ${currentDoc} இல்லாவிட்டால் மாற்று வழி என்ன?`;
                              setSelectedService(null);
                              if (onAskServiceAI) {
                                onAskServiceAI(q);
                              }
                            }}
                          >
                            <Sparkles size={14} color="#059669" />
                            <span>{language === 'ta' ? 'AI-யிடம் விளக்கம் கேட்க' : 'Ask AI'}</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                /* Step Completion Screen: Ready to Apply */
                <div className="wizard-success-card">
                  <div className="wizard-celebration-badge">
                    <Sparkles size={16} color="#15803d" />
                    <span>{language === 'ta' ? 'வாழ்த்துகள்! நீங்கள் விண்ணப்பிக்கலாம்!' : 'Ready to Apply!'}</span>
                  </div>

                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1d1d1f', marginBottom: '0.5rem' }}>
                    {language === 'ta' ? `${selectedService.title_ta} ஆவணங்கள் சரிபார்க்கப்பட்டது` : `${selectedService.title_en} Documents Verified`}
                  </h3>
                  <p style={{ color: '#64748b', fontSize: '0.88rem', marginBottom: '1.25rem' }}>
                    {language === 'ta' 
                      ? 'அரசு கட்டணம் ₹60 செலுத்தி tnesevai.tn.gov.in போர்ட்டலில் அல்லது அருகிலுள்ள இ-சேவை மையத்தில் விண்ணப்பிக்கலாம்.'
                      : 'You are eligible to submit application with govt fee of ₹60 on tnesevai.tn.gov.in.'}
                  </p>

                  {/* Checklist Summary */}
                  <div className="wizard-summary-checklist">
                    {docs.map((doc, idx) => {
                      const hasDoc = docAnswers[idx] !== false;
                      return (
                        <div 
                          key={idx}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                            padding: '8px 12px',
                            background: hasDoc ? '#f0fdf4' : '#fffbeb',
                            borderRadius: '12px',
                            border: `1px solid ${hasDoc ? '#bbf7d0' : '#fef08a'}`,
                            fontSize: '0.86rem'
                          }}
                        >
                          {hasDoc ? (
                            <CheckCircle2 size={18} color="#15803d" />
                          ) : (
                            <AlertCircle size={18} color="#b45309" />
                          )}
                          <span style={{ fontWeight: 600, color: hasDoc ? '#166534' : '#854d0e', flex: 1 }}>
                            {doc}
                          </span>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: hasDoc ? '#15803d' : '#b45309' }}>
                            {hasDoc ? (language === 'ta' ? 'தயாராக உள்ளது' : 'Ready') : (language === 'ta' ? 'மாற்று வழி' : 'Alternative')}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* 3 Application Steps */}
                  <div className="phonepe-card-block" style={{ textAlign: 'left', marginTop: '1.25rem' }}>
                    <div className="block-title">
                      <FileText size={17} color="#0071e3" />
                      <span>{language === 'ta' ? 'அடுத்த 3 எளிய படிகள்:' : 'Next 3 Simple Steps:'}</span>
                    </div>
                    <div className="phonepe-steps-list">
                      {(language === 'ta' ? selectedService.steps_ta : selectedService.steps_en).map((step, idx) => (
                        <div key={idx} className="phonepe-step-row">
                          <span className="step-number">{idx + 1}</span>
                          <span className="step-text">{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="phonepe-modal-actions" style={{ marginTop: '1.5rem' }}>
                    <button
                      type="button"
                      className="phonepe-primary-btn"
                      onClick={() => {
                        const id = selectedService.id;
                        setSelectedService(null);
                        if (onStartService) {
                          onStartService(id);
                        }
                      }}
                    >
                      <CheckCircle2 size={18} />
                      <span>{language === 'ta' ? 'இ-சேவை வழிகாட்டியைத் தொடங்கு' : 'Start Application Task'}</span>
                    </button>

                    <button
                      type="button"
                      className="phonepe-primary-btn"
                      style={{ background: '#0f172a' }}
                      onClick={() => {
                        const q = `${selectedService.title_ta} விண்ணப்பிக்க முழு வழிகாட்டுதல் வேண்டும்.`;
                        setSelectedService(null);
                        if (onAskServiceAI) {
                          onAskServiceAI(q);
                        }
                      }}
                    >
                      <Sparkles size={17} color="#ffb74d" />
                      <span>{language === 'ta' ? 'AI வழிகாட்டியிடம் கேட்க' : 'Ask AI'}</span>
                    </button>

                    <button
                      type="button"
                      className="phonepe-share-btn"
                      onClick={() => {
                        const text = encodeURIComponent(
                          `*நம்ம சேவை AI வழிகாட்டி*\n${selectedService.title_ta}\nகட்டணம்: ${selectedService.fee_ta}\nகாலம்: ${selectedService.days_ta}\n\nசரிபார்க்கப்பட்ட ஆவணங்கள்:\n${selectedService.docs_ta.map(d => '• ' + d).join('\n')}\n\nஅதிகாரப்பூர்வ தளம்: https://tnesevai.tn.gov.in`
                        );
                        window.open(`https://wa.me/?text=${text}`, '_blank');
                      }}
                    >
                      <Share2 size={17} color="#25D366" />
                      <span>WhatsApp</span>
                    </button>

                    <button
                      type="button"
                      className="phonepe-share-btn"
                      style={{ borderColor: '#cbd5e1', color: '#475569' }}
                      onClick={() => {
                        setCurrentDocIndex(0);
                        setDocAnswers({});
                        setWizardFinished(false);
                        setShowHelpNote(null);
                      }}
                      title={language === 'ta' ? 'மீண்டும் சோதிக்க' : 'Restart check'}
                    >
                      <RefreshCw size={16} />
                      <span>{language === 'ta' ? 'மீண்டும் சரிபார்க்க' : 'Restart'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })()}
    </section>
  );
};

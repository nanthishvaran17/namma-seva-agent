export interface ServiceSource {
  title: string;
  publisher: string;
  url: string;
  retrieval_date: string;
}

export interface ServiceFee {
  amount_inr: number;
  is_free: boolean;
  verified_description: string;
}

export interface ProcessingTime {
  working_days: number;
  description_en: string;
  description_ta: string;
}

export interface RequiredDocument {
  doc_code: string;
  name_en: string;
  name_ta: string;
  description?: string;
  mandatory: boolean;
  acceptable_formats?: string[];
}

export interface ApplicationStep {
  step_number: number;
  title_en: string;
  title_ta: string;
  instruction_en: string;
  instruction_ta: string;
  action_url?: string;
}

export interface ServiceItem {
  service_id: string;
  name_en: string;
  name_ta: string;
  description_en: string;
  description_ta: string;
  department: string;
  category: string;
  portal_url: string;
  application_url?: string;
  fee: ServiceFee;
  processing_time: ProcessingTime;
  eligibility_rules: any[];
  required_documents: RequiredDocument[];
  application_steps: ApplicationStep[];
  dependencies: string[];
  official_sources: ServiceSource[];
  verification_status: 'DRAFT' | 'NEEDS_VERIFICATION' | 'VERIFIED' | 'RETIRED';
  last_verified: string;
}

export interface UserTask {
  id: string;
  service_id: string;
  status: string;
  current_step_index: number;
  action_plan: any;
  form_data: Record<string, any>;
  submission_evidence: Record<string, any>;
  next_action_en?: string;
  next_action_ta?: string;
  target_deadline?: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string;
  role: string;
  preferred_language: string;
  created_at: string;
}

export interface ChatMessage {
  id?: string;
  sender: 'USER' | 'AGENT';
  content: string;
  language?: string;
  citations?: { title: string; url: string }[];
  action_cards?: any[];
}

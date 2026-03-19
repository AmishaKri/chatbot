export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id: string;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  subscription_tier: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  organization: Organization;
}

export interface Chatbot {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  system_prompt?: string;
  welcome_message: string;
  tone: string;
  provider: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  streaming_enabled: boolean;
  theme_config?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChatbotCreate {
  name: string;
  system_prompt?: string;
  welcome_message: string;
  tone: string;
  provider: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  streaming_enabled: boolean;
  theme_config?: Record<string, any>;
}

export interface APIKey {
  id: string;
  organization_id: string;
  provider: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  last_used_at?: string;
}

export interface Document {
  id: string;
  chatbot_id: string;
  organization_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  uploaded_at: string;
  processed_at?: string;
}

export interface Conversation {
  id: string;
  chatbot_id: string;
  session_id: string;
  user_identifier?: string;
  started_at: string;
  last_message_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  content: string;
  tokens_used: number;
  created_at: string;
}

export interface AnalyticsOverview {
  total_conversations: number;
  total_messages: number;
  total_tokens_used: number;
  total_estimated_cost: number;
  active_chatbots: number;
}

export interface ProviderUsage {
  provider: string;
  total_tokens: number;
  total_requests: number;
  total_cost: number;
  percentage: number;
}

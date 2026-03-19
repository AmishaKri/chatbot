import api from './api';
import { Conversation, Message } from '@/types';

export const conversationService = {
  list: async (chatbotId?: string): Promise<Conversation[]> => {
    const params = chatbotId ? `?chatbot_id=${chatbotId}` : '';
    const response = await api.get(`/api/chat/conversations${params}`);
    return response.data;
  },

  getMessages: async (conversationId: string): Promise<Message[]> => {
    const response = await api.get(`/api/chat/conversations/${conversationId}/messages`);
    return response.data;
  },

  delete: async (conversationId: string): Promise<void> => {
    await api.delete(`/api/chat/conversations/${conversationId}`);
  },
};

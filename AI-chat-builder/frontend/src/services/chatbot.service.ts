import api from './api';
import { Chatbot, ChatbotCreate } from '@/types';

export const chatbotService = {
  list: async (): Promise<Chatbot[]> => {
    const response = await api.get('/api/chatbots/');
    return response.data;
  },

  get: async (id: string): Promise<Chatbot> => {
    const response = await api.get(`/api/chatbots/${id}`);
    return response.data;
  },

  create: async (data: ChatbotCreate): Promise<Chatbot> => {
    const response = await api.post('/api/chatbots/', data);
    return response.data;
  },

  update: async (id: string, data: Partial<ChatbotCreate>): Promise<Chatbot> => {
    const response = await api.put(`/api/chatbots/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/chatbots/${id}`);
  },

  getEmbedCode: async (id: string) => {
    const response = await api.get(`/api/chatbots/${id}/embed-code`);
    return response.data;
  },
};

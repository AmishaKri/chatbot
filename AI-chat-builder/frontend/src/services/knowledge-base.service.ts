import api from './api';
import { Document } from '@/types';

export interface DocumentUploadResponse {
  id: string;
  filename: string;
  status: string;
  message: string;
}

export const knowledgeBaseService = {
  list: async (chatbotId?: string): Promise<Document[]> => {
    const params = chatbotId ? `?chatbot_id=${chatbotId}` : '';
    const response = await api.get(`/api/knowledge/documents${params}`);
    return response.data;
  },

  upload: async (chatbotId: string, file: File): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/api/knowledge/upload?chatbot_id=${chatbotId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  delete: async (documentId: string): Promise<void> => {
    await api.delete(`/api/knowledge/documents/${documentId}`);
  },

  getStatus: async (documentId: string): Promise<Document> => {
    const response = await api.get(`/api/knowledge/documents/${documentId}/status`);
    return response.data;
  },
};

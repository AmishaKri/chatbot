import api from './api';
import { APIKey } from '@/types';

export interface APIKeyCreate {
  provider: string;
  api_key: string;
  is_default?: boolean;
}

export interface APIKeyUpdate {
  api_key?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface APIKeyTestResult {
  success: boolean;
  message: string;
}

export const apiKeyService = {
  list: async (): Promise<APIKey[]> => {
    const response = await api.get('/api/api-keys/');
    return response.data;
  },

  create: async (data: APIKeyCreate): Promise<APIKey> => {
    const response = await api.post('/api/api-keys/', data);
    return response.data;
  },

  update: async (id: string, data: APIKeyUpdate): Promise<APIKey> => {
    const response = await api.put(`/api/api-keys/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/api-keys/${id}`);
  },

  test: async (id: string): Promise<APIKeyTestResult> => {
    const response = await api.post(`/api/api-keys/${id}/test`);
    return response.data;
  },

  setDefault: async (id: string): Promise<APIKey> => {
    const response = await api.put(`/api/api-keys/${id}/set-default`);
    return response.data;
  },
};

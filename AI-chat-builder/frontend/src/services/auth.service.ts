import api from './api';
import { AuthResponse } from '@/types';

export const authService = {
  register: async (data: {
    organization_name: string;
    email: string;
    password: string;
    full_name: string;
  }): Promise<AuthResponse> => {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  logout: async () => {
    await api.post('/api/auth/logout');
    localStorage.removeItem('token');
  },
};

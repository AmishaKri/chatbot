import { create } from 'zustand';
import { User, Organization } from '@/types';

interface AuthState {
  user: User | null;
  organization: Organization | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, organization: Organization, token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  organization: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  setAuth: (user, organization, token) => {
    localStorage.setItem('token', token);
    set({ user, organization, token, isAuthenticated: true });
  },
  clearAuth: () => {
    localStorage.removeItem('token');
    set({ user: null, organization: null, token: null, isAuthenticated: false });
  },
}));

import api from './api';
import { AnalyticsOverview, ProviderUsage } from '@/types';

export const analyticsService = {
  getOverview: async (): Promise<AnalyticsOverview> => {
    const response = await api.get('/api/analytics/overview');
    return response.data;
  },

  getProviderUsage: async (days: number = 30): Promise<ProviderUsage[]> => {
    const response = await api.get(`/api/analytics/usage?days=${days}`);
    return response.data;
  },

  getCostBreakdown: async (days: number = 30) => {
    const response = await api.get(`/api/analytics/costs?days=${days}`);
    return response.data;
  },

  getConversationStats: async () => {
    const response = await api.get('/api/analytics/conversations/stats');
    return response.data;
  },
};

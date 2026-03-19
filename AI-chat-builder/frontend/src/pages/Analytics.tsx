import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '@/services/analytics.service';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

export default function Analytics() {
  const { data: providerUsage } = useQuery({
    queryKey: ['analytics', 'provider-usage'],
    queryFn: () => analyticsService.getProviderUsage(30),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Provider Usage</h2>
          {providerUsage && providerUsage.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={providerUsage}
                  dataKey="total_tokens"
                  nameKey="provider"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {providerUsage.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-12">No data available</p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost Breakdown</h2>
          <div className="space-y-3">
            {providerUsage?.map((provider) => (
              <div key={provider.provider} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium capitalize">{provider.provider}</span>
                <span className="text-gray-600">${provider.total_cost.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

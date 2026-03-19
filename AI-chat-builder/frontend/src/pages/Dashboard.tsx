import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '@/services/analytics.service';
import { chatbotService } from '@/services/chatbot.service';
import { Bot, MessageSquare, DollarSign, TrendingUp } from 'lucide-react';

export default function Dashboard() {
  const { data: overview } = useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: analyticsService.getOverview,
  });

  const { data: chatbots } = useQuery({
    queryKey: ['chatbots'],
    queryFn: chatbotService.list,
  });

  const stats = [
    {
      name: 'Active Chatbots',
      value: overview?.active_chatbots || 0,
      icon: Bot,
      color: 'bg-blue-500',
    },
    {
      name: 'Total Conversations',
      value: overview?.total_conversations || 0,
      icon: MessageSquare,
      color: 'bg-green-500',
    },
    {
      name: 'Total Messages',
      value: overview?.total_messages || 0,
      icon: TrendingUp,
      color: 'bg-purple-500',
    },
    {
      name: 'Estimated Cost',
      value: `$${(overview?.total_estimated_cost || 0).toFixed(4)}`,
      icon: DollarSign,
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">Welcome to your AI Chat Builder</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`${stat.color} p-3 rounded-lg`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Chatbots</h2>
          <div className="space-y-4">
            {chatbots?.slice(0, 5).map((chatbot) => (
              <div key={chatbot.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-medium text-gray-900">{chatbot.name}</h3>
                  <p className="text-sm text-gray-500">
                    {chatbot.provider} • {chatbot.model_name}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    chatbot.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {chatbot.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

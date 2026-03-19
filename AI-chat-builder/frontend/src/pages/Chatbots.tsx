import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { chatbotService } from '@/services/chatbot.service';
import { Plus, Edit, Trash2, Code2, Bot, Loader2, X, Copy, Check, MessageSquare } from 'lucide-react';

const PROVIDER_BADGE: Record<string, string> = {
  groq: 'bg-orange-100 text-orange-700',
  gemini: 'bg-blue-100 text-blue-700',
  together: 'bg-purple-100 text-purple-700',
  grok: 'bg-indigo-100 text-indigo-700',
};

export default function Chatbots() {
  const queryClient = useQueryClient();
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [embedChatbot, setEmbedChatbot] = useState<{ id: string; name: string } | null>(null);
  const [embedCode, setEmbedCode] = useState('');
  const [copied, setCopied] = useState(false);

  const { data: chatbots, isLoading } = useQuery({
    queryKey: ['chatbots'],
    queryFn: chatbotService.list,
  });

  const deleteMutation = useMutation({
    mutationFn: chatbotService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
      setDeleteConfirm(null);
    },
  });

  const handleGetEmbedCode = async (id: string, name: string) => {
    setEmbedChatbot({ id, name });
    try {
      const data = await chatbotService.getEmbedCode(id);
      setEmbedCode(data.embed_code);
    } catch {
      setEmbedCode('');
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Chatbots</h1>
          <p className="mt-1 text-gray-600">Manage your AI chatbots</p>
        </div>
        <Link
          to="/chatbots/new"
          className="inline-flex items-center gap-2 px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Create Chatbot
        </Link>
      </div>

      {chatbots?.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Bot className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-1">No chatbots yet</h3>
          <p className="text-gray-500 mb-6 text-sm">
            Create your first AI chatbot to get started.
          </p>
          <Link
            to="/chatbots/new"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Chatbot
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {chatbots?.map((chatbot) => (
            <div key={chatbot.id} className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-5">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="bg-primary/10 p-2 rounded-lg flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-900 truncate">{chatbot.name}</h3>
                </div>
                <span className={`ml-2 flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${
                  chatbot.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                }`}>
                  {chatbot.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="space-y-1.5 mb-4">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${
                    PROVIDER_BADGE[chatbot.provider] || 'bg-gray-100 text-gray-600'
                  }`}>
                    {chatbot.provider}
                  </span>
                  <span className="text-xs text-gray-500 truncate">{chatbot.model_name.split('/').pop()}</span>
                </div>
                <p className="text-xs text-gray-500 capitalize">
                  {chatbot.tone} tone • Temp {chatbot.temperature}
                </p>
                {chatbot.system_prompt && (
                  <p className="text-xs text-gray-400 line-clamp-2">{chatbot.system_prompt}</p>
                )}
              </div>

              <div className="flex gap-2 pt-3 border-t border-gray-100">
                <Link
                  to={`/chatbots/${chatbot.id}/edit`}
                  className="flex-1 inline-flex justify-center items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                >
                  <Edit className="w-3.5 h-3.5" />
                  Edit
                </Link>
                <Link
                  to={`/chatbots/${chatbot.id}/edit?preview=1`}
                  className="flex-1 inline-flex justify-center items-center gap-1.5 px-3 py-2 border border-indigo-200 rounded-lg text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors"
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  Preview
                </Link>
                <button
                  onClick={() => handleGetEmbedCode(chatbot.id, chatbot.name)}
                  className="flex-1 inline-flex justify-center items-center gap-1.5 px-3 py-2 border border-gray-300 rounded-lg text-xs font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                >
                  <Code2 className="w-3.5 h-3.5" />
                  Embed
                </button>
                {deleteConfirm === chatbot.id ? (
                  <div className="flex gap-1">
                    <button
                      onClick={() => deleteMutation.mutate(chatbot.id)}
                      disabled={deleteMutation.isPending}
                      className="px-2 py-2 text-xs font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center"
                    >
                      {deleteMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Yes'}
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(null)}
                      className="px-2 py-2 text-xs font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      No
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setDeleteConfirm(chatbot.id)}
                    className="px-3 py-2 border border-red-200 rounded-lg text-xs font-medium text-red-600 bg-white hover:bg-red-50 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {embedChatbot && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Embed "{embedChatbot.name}"</h2>
              <button
                onClick={() => setEmbedChatbot(null)}
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Add this script tag to your website to embed the chatbot widget.
            </p>
            <div className="relative bg-gray-900 rounded-lg p-4">
              <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap break-all">
                {embedCode || 'Loading...'}
              </pre>
              <button
                onClick={handleCopy}
                className="absolute top-2 right-2 p-1.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 hover:text-white transition-colors"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-3">
              The widget will appear as a floating chat button on your site.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

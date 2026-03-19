import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiKeyService } from '@/services/api-key.service';
import { APIKey } from '@/types';
import {
  Plus, Trash2, CheckCircle, XCircle, Star, Loader2, Eye, EyeOff,
  ExternalLink, Shield, Key,
} from 'lucide-react';

const PROVIDERS = [
  {
    id: 'together',
    name: 'Together.ai',
    description: 'Primary provider (default) for open-source AI models at scale',
    docsUrl: 'https://api.together.xyz/settings/api-keys',
    badge: 'bg-purple-100 text-purple-800',
    models: ['mistralai/Mixtral-8x7B-Instruct-v0.1', 'meta-llama/Llama-3-70b-chat-hf'],
  },
  {
    id: 'grok',
    name: 'xAI Grok',
    description: 'xAI Grok models for fast reasoning and real-time intelligence',
    docsUrl: 'https://console.x.ai/',
    badge: 'bg-indigo-100 text-indigo-800',
    models: ['grok-2-latest', 'grok-beta'],
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    description: "Google's most capable multimodal AI models",
    docsUrl: 'https://aistudio.google.com/app/apikey',
    badge: 'bg-blue-100 text-blue-800',
    models: ['gemini-1.5-pro', 'gemini-1.5-flash'],
  },
  {
    id: 'groq',
    name: 'Groq',
    description: 'Ultra-fast AI inference with Llama and Mixtral models',
    docsUrl: 'https://console.groq.com/keys',
    badge: 'bg-orange-100 text-orange-800',
    models: ['llama-3.1-8b-instant', 'llama-3.1-70b-versatile'],
  },
];

export default function ProviderSettings() {
  const queryClient = useQueryClient();
  const [addingProvider, setAddingProvider] = useState<string | null>(null);
  const [newApiKey, setNewApiKey] = useState('');
  const [isDefault, setIsDefault] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: apiKeyService.list,
  });

  const createMutation = useMutation({
    mutationFn: (data: { provider: string; api_key: string; is_default: boolean }) =>
      apiKeyService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      setAddingProvider(null);
      setNewApiKey('');
      setIsDefault(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: apiKeyService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      setDeleteConfirm(null);
    },
  });

  const setDefaultMutation = useMutation({
    mutationFn: apiKeyService.setDefault,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
    },
  });

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const result = await apiKeyService.test(id);
      setTestResults((prev) => ({ ...prev, [id]: result }));
    } catch {
      setTestResults((prev) => ({ ...prev, [id]: { success: false, message: 'Test failed' } }));
    } finally {
      setTestingId(null);
    }
  };

  const handleAddKey = (providerId: string) => {
    if (!newApiKey.trim()) return;
    createMutation.mutate({ provider: providerId, api_key: newApiKey.trim(), is_default: isDefault });
  };

  const getKeysForProvider = (providerId: string): APIKey[] =>
    apiKeys?.filter((k) => k.provider === providerId) || [];

  const openAdd = (providerId: string) => {
    setAddingProvider(addingProvider === providerId ? null : providerId);
    setNewApiKey('');
    setShowKey(false);
    // setIsDefault(!hasKeys);
    createMutation.reset();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-start gap-3">
        <div className="bg-primary/10 p-3 rounded-lg">
          <Key className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Provider Settings</h1>
          <p className="mt-1 text-gray-600">
            Manage API keys for AI providers. Keys are encrypted and stored securely.
          </p>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex gap-3">
        <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-blue-700">
          API keys are encrypted before being stored. You must configure at least one provider key
          before creating chatbots using that provider.
        </p>
      </div>

      {PROVIDERS.map((provider) => {
        const keys = getKeysForProvider(provider.id);
        const isAdding = addingProvider === provider.id;

        return (
          <div key={provider.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${provider.badge}`}>
                    {provider.name}
                  </span>
                  <p className="text-sm text-gray-500 hidden sm:block">{provider.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    keys.length > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {keys.length} key{keys.length !== 1 ? 's' : ''}
                  </span>
                  <button
                    onClick={() => openAdd(provider.id)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Add Key
                  </button>
                </div>
              </div>
            </div>

            {isAdding && (
              <div className="p-6 bg-gray-50 border-b border-gray-200">
                <div className="space-y-4 max-w-lg">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-sm font-medium text-gray-700">API Key</label>
                      <a
                        href={provider.docsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-primary hover:underline"
                      >
                        Get your key <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                    <div className="relative">
                      <input
                        type={showKey ? 'text' : 'password'}
                        value={newApiKey}
                        onChange={(e) => setNewApiKey(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddKey(provider.id)}
                        placeholder="Paste your API key here..."
                        className="block w-full px-3 py-2 border border-gray-300 rounded-lg pr-10 focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => setShowKey(!showKey)}
                        className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                      >
                        {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id={`default-${provider.id}`}
                      checked={isDefault}
                      onChange={(e) => setIsDefault(e.target.checked)}
                      className="rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <label htmlFor={`default-${provider.id}`} className="text-sm text-gray-700">
                      Set as default key for {provider.name}
                    </label>
                  </div>

                  {createMutation.isError && (
                    <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                      {(createMutation.error as any)?.response?.data?.detail || 'Failed to save API key'}
                    </p>
                  )}

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAddKey(provider.id)}
                      disabled={!newApiKey.trim() || createMutation.isPending}
                      className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
                    >
                      {createMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      Save Key
                    </button>
                    <button
                      onClick={() => { setAddingProvider(null); setNewApiKey(''); }}
                      className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="p-6">
              {keys.length === 0 ? (
                <div className="text-center py-6">
                  <Key className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No API keys configured for {provider.name}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    Add a key above to enable chatbots using this provider
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {keys.map((key) => (
                    <div
                      key={key.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${key.is_active ? 'bg-green-500' : 'bg-gray-300'}`} />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-mono text-gray-700">
                              ••••••••••••{key.id.slice(-6)}
                            </span>
                            {key.is_default && (
                              <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded-full flex items-center gap-1 font-medium">
                                <Star className="w-3 h-3" /> Default
                              </span>
                            )}
                            {!key.is_active && (
                              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full font-medium">
                                Inactive
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 mt-0.5">
                            Added {new Date(key.created_at).toLocaleDateString()}
                            {key.last_used_at && ` • Last used ${new Date(key.last_used_at).toLocaleDateString()}`}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                        {testResults[key.id] && (
                          <span className={`flex items-center gap-1 text-xs font-medium ${
                            testResults[key.id].success ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {testResults[key.id].success
                              ? <CheckCircle className="w-4 h-4" />
                              : <XCircle className="w-4 h-4" />
                            }
                            <span className="hidden sm:inline">{testResults[key.id].message}</span>
                          </span>
                        )}

                        <button
                          onClick={() => handleTest(key.id)}
                          disabled={testingId === key.id}
                          className="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1 transition-colors"
                        >
                          {testingId === key.id
                            ? <Loader2 className="w-3 h-3 animate-spin" />
                            : null
                          }
                          Test
                        </button>

                        {!key.is_default && (
                          <button
                            onClick={() => setDefaultMutation.mutate(key.id)}
                            disabled={setDefaultMutation.isPending}
                            title="Set as default"
                            className="px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-yellow-50 hover:border-yellow-300 hover:text-yellow-800 disabled:opacity-50 transition-colors"
                          >
                            Set Default
                          </button>
                        )}

                        {deleteConfirm === key.id ? (
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => deleteMutation.mutate(key.id)}
                              disabled={deleteMutation.isPending}
                              className="px-2 py-1.5 text-xs font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
                            >
                              {deleteMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Confirm'}
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="px-2 py-1.5 text-xs font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(key.id)}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete key"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

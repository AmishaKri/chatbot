import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { chatbotService } from '@/services/chatbot.service';
import { apiKeyService } from '@/services/api-key.service';
import { AlertCircle, ChevronRight, Bot, Loader2, Info, Send, Sparkles, RotateCcw } from 'lucide-react';

const PROVIDER_MODELS: Record<string, { value: string; label: string; description: string }[]> = {
  gemini: [
    { value: 'gemini-3-flash-preview', label: 'Gemini 3 Flash Preview', description: 'Fast multimodal with free input/output and caching' },
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', description: 'Multimodal with up to 1M context window' },
    { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash-Lite', description: 'Lightweight, cost-effective model for scale' },
  ],
  grok: [
    { value: 'grok-4-latest', label: 'Grok 4 Latest', description: 'Latest flagship Grok model' },

  ],
  together: [
    { value: 'Qwen/Qwen2.5-7B-Instruct-Turbo', label: 'Qwen 2.5 7B Turbo', description: 'Fast and affordable' },
    { value: 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo', label: 'Llama 3.1 8B Turbo', description: 'Good low-cost default' },
    { value: 'mistralai/Mixtral-8x7B-Instruct-v0.1', label: 'Mixtral 8x7B', description: 'Higher cost / usage limits' },
  ],
  groq: [
    { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant', description: 'Best free-tier reliability' },
    { value: 'gemma2-9b-it', label: 'Gemma 2 9B', description: 'Strong free-tier fallback' },
  ],
};

const DEFAULT_MODELS: Record<string, string> = {
  gemini: 'gemini-3-flash-preview',
  grok: 'grok-4-latest',
  together: 'Qwen/Qwen2.5-7B-Instruct-Turbo',
  groq: 'llama-3.1-8b-instant',
};

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'casual', label: 'Casual' },
  { value: 'formal', label: 'Formal' },
  { value: 'empathetic', label: 'Empathetic' },
];

export default function ChatbotBuilder() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditing = Boolean(id);
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    system_prompt: '',
    welcome_message: 'Hello! How can I help you today?',
    tone: 'professional',
    provider: 'groq',
    model_name: 'llama-3.1-8b-instant',
    temperature: 0.7,
    max_tokens: 1000,
    streaming_enabled: true,
  });
  const [previewInput, setPreviewInput] = useState('');
  const [previewSessionId, setPreviewSessionId] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [lastPreviewSyncedSignature, setLastPreviewSyncedSignature] = useState('');
  const [previewMessages, setPreviewMessages] = useState<Array<{ id: string; role: 'user' | 'assistant'; content: string }>>([
    { id: 'welcome', role: 'assistant', content: 'Hello! How can I help you today?' },
  ]);

  const getPreviewConfigSignature = (data: typeof formData) =>
    JSON.stringify({
      system_prompt: data.system_prompt,
      welcome_message: data.welcome_message,
      tone: data.tone,
      provider: data.provider,
      model_name: data.model_name,
      temperature: data.temperature,
      max_tokens: data.max_tokens,
      streaming_enabled: data.streaming_enabled,
    });

  const { data: existingChatbot, isLoading: loadingChatbot } = useQuery({
    queryKey: ['chatbot', id],
    queryFn: () => chatbotService.get(id!),
    enabled: isEditing,
  });

  const { data: apiKeys } = useQuery({
    queryKey: ['api-keys'],
    queryFn: apiKeyService.list,
  });

  useEffect(() => {
    if (existingChatbot) {
      const nextFormData = {
        name: existingChatbot.name,
        system_prompt: existingChatbot.system_prompt || '',
        welcome_message: existingChatbot.welcome_message,
        tone: existingChatbot.tone,
        provider: existingChatbot.provider,
        model_name: existingChatbot.model_name,
        temperature: existingChatbot.temperature,
        max_tokens: existingChatbot.max_tokens,
        streaming_enabled: existingChatbot.streaming_enabled,
      };
      setFormData(nextFormData);
      setLastPreviewSyncedSignature(getPreviewConfigSignature(nextFormData));
      setPreviewMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: existingChatbot.welcome_message || 'Hello! How can I help you today?',
        },
      ]);
      setPreviewSessionId(null);
      setPreviewError('');
    }
  }, [existingChatbot]);

  useEffect(() => {
    setPreviewMessages((prev) => {
      if (prev.length === 1 && prev[0].id === 'welcome') {
        return [{ ...prev[0], content: formData.welcome_message || 'Hello! How can I help you today?' }];
      }
      return prev;
    });
  }, [formData.welcome_message]);

  const hasKeyForProvider = (provider: string) =>
    apiKeys?.some((k) => k.provider === provider && k.is_active) ?? null;

  const handleProviderChange = (provider: string) => {
    setFormData({
      ...formData,
      provider,
      model_name: DEFAULT_MODELS[provider] || '',
    });
  };

  const resetPreview = () => {
    setPreviewSessionId(null);
    setPreviewError('');
    setPreviewInput('');
    setPreviewMessages([
      { id: 'welcome', role: 'assistant', content: formData.welcome_message || 'Hello! How can I help you today?' },
    ]);
  };

  const appendAssistantChunk = (assistantId: string, chunk: string) => {
    setPreviewMessages((prev) =>
      prev.map((msg) =>
        msg.id === assistantId ? { ...msg, content: msg.content + chunk } : msg
      )
    );
  };

  const handlePreviewSend = async () => {
    const message = previewInput.trim();
    if (!message || previewLoading || !id) return;

    setPreviewError('');
    setPreviewLoading(true);
    let assistantId: string | null = null;

    try {
      const currentSignature = getPreviewConfigSignature(formData);
      if (currentSignature !== lastPreviewSyncedSignature) {
        await chatbotService.update(id, formData);
        setLastPreviewSyncedSignature(currentSignature);
        setPreviewSessionId(null);
      }

      assistantId = `assistant-${Date.now()}`;
      setPreviewInput('');
      setPreviewMessages((prev) => [
        ...prev,
        { id: `user-${Date.now()}`, role: 'user', content: message },
        { id: assistantId!, role: 'assistant', content: '' },
      ]);

      const response = await fetch(`${API_URL}/api/public/chat/${id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: previewSessionId,
          user_identifier: 'builder-preview',
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Failed to start preview chat.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          const dataLine = event
            .split('\n')
            .find((line) => line.startsWith('data:'));

          if (!dataLine) continue;

          const raw = dataLine.replace(/^data:\s?/, '');
          if (!raw) continue;

          const payload = JSON.parse(raw);

          if (payload.type === 'chunk' && payload.content) {
            appendAssistantChunk(assistantId, payload.content);
          }

          if (payload.session_id) {
            setPreviewSessionId(payload.session_id);
          }

          if (payload.type === 'error') {
            throw new Error(payload.content || 'Preview chat failed.');
          }
        }
      }

      setPreviewMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId && !msg.content
            ? { ...msg, content: 'No response from model.' }
            : msg
        )
      );
    } catch (err: any) {
      const messageText = err?.message || 'Preview chat failed.';
      setPreviewError(messageText);
      if (assistantId) {
        setPreviewMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: `Error: ${messageText}` }
              : msg
          )
        );
      }
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isEditing) {
        await chatbotService.update(id!, formData);
      } else {
        await chatbotService.create(formData);
      }
      navigate('/chatbots');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || `Failed to ${isEditing ? 'update' : 'create'} chatbot. Please try again.`;
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (isEditing && loadingChatbot) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const providerHasKey = hasKeyForProvider(formData.provider);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/chatbots" className="hover:text-gray-700">Chatbots</Link>
        <ChevronRight className="w-4 h-4" />
        <span className="text-gray-900 font-medium">{isEditing ? 'Edit Chatbot' : 'Create Chatbot'}</span>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <div className="bg-primary/10 p-2.5 rounded-lg">
          <Bot className="w-6 h-6 text-primary" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900">
          {isEditing ? `Edit "${existingChatbot?.name}"` : 'Create Chatbot'}
        </h1>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-2">
          <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium">{isEditing ? 'Error updating chatbot' : 'Error creating chatbot'}</p>
            <p className="text-sm mt-1">{error}</p>
            {error.includes('API key') && (
              <Link to="/providers" className="text-sm underline mt-1 inline-block">
                Go to Provider Settings →
              </Link>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
          <h2 className="text-lg font-semibold text-gray-900 pb-2 border-b border-gray-100">Basic Information</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chatbot Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Customer Support Bot"
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tone</label>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
              {TONES.map((tone) => (
                <button
                  key={tone.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, tone: tone.value })}
                  className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                    formData.tone === tone.value
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                  }`}
                >
                  {tone.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
            <textarea
              rows={4}
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
              placeholder="You are a helpful customer support assistant for Acme Corp. Always be polite and professional..."
            />
            <p className="text-xs text-gray-400 mt-1">
              Define the chatbot's persona, role, and behavior guidelines.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Welcome Message</label>
            <input
              type="text"
              value={formData.welcome_message}
              onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
            />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
          <h2 className="text-lg font-semibold text-gray-900 pb-2 border-b border-gray-100">AI Model</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Provider</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { id: 'together', name: 'Together', color: 'purple' },
                { id: 'grok', name: 'Grok', color: 'indigo' },
                { id: 'gemini', name: 'Gemini', color: 'blue' },
                { id: 'groq', name: 'Groq', color: 'orange' },
              ].map((p) => {
                const hasKey = hasKeyForProvider(p.id);
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleProviderChange(p.id)}
                    className={`relative p-3 rounded-lg border-2 text-sm font-medium transition-colors ${
                      formData.provider === p.id
                        ? 'border-primary bg-primary/5 text-primary'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {p.name}
                    {p.id === 'together' && (
                      <span className="ml-1 text-[10px] align-middle px-1.5 py-0.5 rounded bg-primary/10 text-primary font-semibold">
                        Primary
                      </span>
                    )}
                    <span className={`absolute top-1 right-1 w-2 h-2 rounded-full ${
                      hasKey === null ? 'bg-gray-300' : hasKey ? 'bg-green-500' : 'bg-red-400'
                    }`} title={hasKey ? 'API key configured' : 'No API key'} />
                  </button>
                );
              })}
            </div>
            {providerHasKey === false && (
              <div className="mt-2 flex items-start gap-2 text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <p className="text-xs">
                  No API key for {formData.provider}.{' '}
                  <Link to="/providers" className="underline font-medium">
                    Add one in Provider Settings
                  </Link>{' '}
                  before creating this chatbot.
                </p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
            <select
              value={formData.model_name}
              onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
            >
              {(PROVIDER_MODELS[formData.provider] || []).map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label} — {model.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">
                Temperature
              </label>
              <span className="text-sm font-semibold text-primary">{formData.temperature.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={formData.temperature}
              onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
              className="block w-full accent-primary"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Focused (0.0)</span>
              <span>Creative (1.0)</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Tokens
            </label>
            <input
              type="number"
              min="100"
              max="8192"
              step="100"
              value={formData.max_tokens}
              onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary text-sm"
            />
            <p className="text-xs text-gray-400 mt-1">Maximum response length per message.</p>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-700">Streaming Responses</p>
              <p className="text-xs text-gray-500">Show responses as they are generated</p>
            </div>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, streaming_enabled: !formData.streaming_enabled })}
              className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ${
                formData.streaming_enabled ? 'bg-primary' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform duration-200 ${
                  formData.streaming_enabled ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-primary" />
                Chat Preview
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Test the chatbot behavior live.
              </p>
            </div>
            <button
              type="button"
              onClick={resetPreview}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
          </div>

          {!isEditing ? (
            <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Save the chatbot first, then open edit mode to use live preview chat.
            </div>
          ) : (
            <>
              <div className="h-72 overflow-y-auto border border-gray-200 rounded-lg bg-gray-50 p-3 space-y-3">
                {previewMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] px-3 py-2 rounded-xl text-sm whitespace-pre-wrap ${
                        msg.role === 'user'
                          ? 'bg-primary text-white rounded-tr-sm'
                          : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'
                      }`}
                    >
                      {msg.content || (previewLoading && msg.role === 'assistant' ? 'Typing...' : '')}
                    </div>
                  </div>
                ))}
              </div>

              {previewError && (
                <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-2.5 py-2">
                  {previewError}
                </p>
              )}

              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={previewInput}
                  onChange={(e) => setPreviewInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handlePreviewSend();
                    }
                  }}
                  placeholder="Type a test message..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
                <button
                  type="button"
                  onClick={handlePreviewSend}
                  disabled={!previewInput.trim() || previewLoading}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {previewLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Send
                </button>
              </div>
            </>
          )}
        </div>

        <div className="flex justify-end gap-3 pb-6">
          <button
            type="button"
            onClick={() => navigate('/chatbots')}
            className="px-5 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            {loading
              ? isEditing ? 'Saving...' : 'Creating...'
              : isEditing ? 'Save Changes' : 'Create Chatbot'
            }
          </button>
        </div>
      </form>
    </div>
  );
}

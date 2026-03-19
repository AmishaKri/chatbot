import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { conversationService } from '@/services/conversation.service';
import { chatbotService } from '@/services/chatbot.service';
import { Conversation, Message } from '@/types';
import {
  MessageSquare, ChevronDown, ChevronUp, Trash2, Loader2,
  User, Bot, Search, Filter,
} from 'lucide-react';

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
        isUser ? 'bg-primary text-white' : 'bg-gray-200 text-gray-600'
      }`}>
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>
      <div className={`max-w-[75%] px-3 py-2 rounded-xl text-sm ${
        isUser
          ? 'bg-primary text-white rounded-tr-sm'
          : 'bg-gray-100 text-gray-800 rounded-tl-sm'
      }`}>
        <p className="whitespace-pre-wrap">{message.content}</p>
        <p className={`text-xs mt-1 ${isUser ? 'text-primary-foreground/70' : 'text-gray-400'}`}>
          {new Date(message.created_at).toLocaleTimeString()}
          {message.tokens_used > 0 && ` • ${message.tokens_used} tokens`}
        </p>
      </div>
    </div>
  );
}

function ConversationRow({ conversation, chatbotName, onDelete }: {
  conversation: Conversation;
  chatbotName: string;
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const { data: messages, isLoading: loadingMessages } = useQuery({
    queryKey: ['messages', conversation.id],
    queryFn: () => conversationService.getMessages(conversation.id),
    enabled: expanded,
  });

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <div
        className="flex items-center justify-between p-4 bg-white hover:bg-gray-50 cursor-pointer transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="bg-primary/10 p-2 rounded-lg flex-shrink-0">
            <MessageSquare className="w-4 h-4 text-primary" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-gray-900 truncate">
                {conversation.user_identifier || 'Anonymous User'}
              </span>
              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">
                {chatbotName}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Started {new Date(conversation.started_at).toLocaleString()}
              {' • '}
              Last activity {new Date(conversation.last_message_at).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-3" onClick={(e) => e.stopPropagation()}>
          {deleteConfirm ? (
            <div className="flex gap-1">
              <button
                onClick={() => onDelete(conversation.id)}
                className="px-2 py-1 text-xs font-medium text-white bg-red-600 rounded hover:bg-red-700"
              >
                Delete
              </button>
              <button
                onClick={() => setDeleteConfirm(false)}
                className="px-2 py-1 text-xs font-medium text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setDeleteConfirm(true)}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
          <div className="text-gray-400">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50 p-4 max-h-96 overflow-y-auto">
          {loadingMessages ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : messages && messages.length > 0 ? (
            <div className="space-y-3">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-4">No messages found</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function Conversations() {
  const queryClient = useQueryClient();
  const [selectedChatbot, setSelectedChatbot] = useState('');
  const [search, setSearch] = useState('');

  const { data: chatbots } = useQuery({
    queryKey: ['chatbots'],
    queryFn: chatbotService.list,
  });

  const { data: conversations, isLoading } = useQuery({
    queryKey: ['conversations', selectedChatbot],
    queryFn: () => conversationService.list(selectedChatbot || undefined),
  });

  const deleteMutation = useMutation({
    mutationFn: conversationService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });

  const chatbotMap = Object.fromEntries(
    (chatbots || []).map((c) => [c.id, c.name])
  );

  const filtered = conversations?.filter((conv) => {
    if (!search) return true;
    const name = conv.user_identifier || '';
    return name.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Conversations</h1>
        <p className="mt-1 text-gray-600">View and manage all chatbot conversations</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by user..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <select
            value={selectedChatbot}
            onChange={(e) => setSelectedChatbot(e.target.value)}
            className="pl-9 pr-8 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary bg-white appearance-none cursor-pointer min-w-[180px]"
          >
            <option value="">All Chatbots</option>
            {chatbots?.map((bot) => (
              <option key={bot.id} value={bot.id}>{bot.name}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : filtered?.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-1">No conversations yet</h3>
          <p className="text-sm text-gray-500">
            Conversations will appear here once users start chatting with your chatbots.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">{filtered?.length} conversation{filtered?.length !== 1 ? 's' : ''}</p>
          {filtered?.map((conv) => (
            <ConversationRow
              key={conv.id}
              conversation={conv}
              chatbotName={chatbotMap[conv.chatbot_id] || 'Unknown Bot'}
              onDelete={(id) => deleteMutation.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

import { useState, useRef, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { knowledgeBaseService } from '@/services/knowledge-base.service';
import { chatbotService } from '@/services/chatbot.service';
import { Document } from '@/types';
import {
  Upload, FileText, Trash2, Loader2, CheckCircle, Clock,
  XCircle, BookOpen, AlertCircle, RefreshCw,
} from 'lucide-react';

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; label: string; className: string }> = {
  processing: {
    icon: <Clock className="w-3.5 h-3.5" />,
    label: 'Processing',
    className: 'bg-yellow-100 text-yellow-700',
  },
  completed: {
    icon: <CheckCircle className="w-3.5 h-3.5" />,
    label: 'Ready',
    className: 'bg-green-100 text-green-700',
  },
  failed: {
    icon: <XCircle className="w-3.5 h-3.5" />,
    label: 'Failed',
    className: 'bg-red-100 text-red-700',
  },
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function DocumentRow({ doc, onDelete, onRefresh }: {
  doc: Document;
  onDelete: (id: string) => void;
  onRefresh: (id: string) => void;
}) {
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const status = STATUS_CONFIG[doc.status] || STATUS_CONFIG.processing;

  return (
    <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors bg-white">
      <div className="flex items-center gap-3 min-w-0">
        <div className="bg-blue-50 p-2 rounded-lg flex-shrink-0">
          <FileText className="w-5 h-5 text-blue-600" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${status.className}`}>
              {status.icon}
              {status.label}
            </span>
            <span className="text-xs text-gray-400">
              {formatBytes(doc.file_size)} • {doc.file_type.toUpperCase()}
            </span>
            <span className="text-xs text-gray-400">
              {new Date(doc.uploaded_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0 ml-3">
        {doc.status === 'processing' && (
          <button
            onClick={() => onRefresh(doc.id)}
            title="Refresh status"
            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
        {deleteConfirm ? (
          <div className="flex gap-1">
            <button
              onClick={() => onDelete(doc.id)}
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
      </div>
    </div>
  );
}

export default function KnowledgeBase() {
  const queryClient = useQueryClient();
  const [selectedChatbot, setSelectedChatbot] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: chatbots } = useQuery({
    queryKey: ['chatbots'],
    queryFn: chatbotService.list,
  });

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents', selectedChatbot],
    queryFn: () => knowledgeBaseService.list(selectedChatbot || undefined),
  });

  const uploadMutation = useMutation({
    mutationFn: ({ chatbotId, file }: { chatbotId: string; file: File }) =>
      knowledgeBaseService.upload(chatbotId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setUploadError('');
    },
    onError: (err: any) => {
      setUploadError(err.response?.data?.detail || 'Upload failed. Please try again.');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: knowledgeBaseService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleRefresh = async (docId: string) => {
    const updated = await knowledgeBaseService.getStatus(docId);
    queryClient.setQueryData(['documents', selectedChatbot], (old: Document[] | undefined) =>
      old?.map((d) => (d.id === docId ? updated : d))
    );
  };

  const handleFiles = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    if (!selectedChatbot) {
      setUploadError('Please select a chatbot first before uploading documents.');
      return;
    }
    setUploadError('');
    Array.from(files).forEach((file) => {
      uploadMutation.mutate({ chatbotId: selectedChatbot, file });
    });
  }, [selectedChatbot, uploadMutation]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const readyCounts = documents?.filter((d) => d.status === 'completed').length ?? 0;
  const processingCounts = documents?.filter((d) => d.status === 'processing').length ?? 0;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-start gap-3">
        <div className="bg-primary/10 p-3 rounded-lg">
          <BookOpen className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="mt-1 text-gray-600">
            Upload documents to enable RAG (retrieval-augmented generation) for your chatbots.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Chatbot</label>
          <select
            value={selectedChatbot}
            onChange={(e) => setSelectedChatbot(e.target.value)}
            className="block w-full max-w-sm px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary bg-white"
          >
            <option value="">All Chatbots</option>
            {chatbots?.map((bot) => (
              <option key={bot.id} value={bot.id}>{bot.name}</option>
            ))}
          </select>
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-primary bg-primary/5'
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.txt"
            onChange={(e) => handleFiles(e.target.files)}
            className="hidden"
          />
          <div className={`w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 ${
            isDragging ? 'bg-primary/10' : 'bg-gray-100'
          }`}>
            {uploadMutation.isPending
              ? <Loader2 className="w-6 h-6 animate-spin text-primary" />
              : <Upload className={`w-6 h-6 ${isDragging ? 'text-primary' : 'text-gray-400'}`} />
            }
          </div>
          <p className="text-sm font-medium text-gray-700 mb-1">
            {uploadMutation.isPending ? 'Uploading...' : 'Drop files here or click to upload'}
          </p>
          <p className="text-xs text-gray-400">Supports PDF, DOCX, DOC, TXT • Max 10MB per file</p>
        </div>

        {uploadError && (
          <div className="mt-3 flex items-start gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p className="text-sm">{uploadError}</p>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Documents</h2>
          {documents && documents.length > 0 && (
            <div className="flex gap-3 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <CheckCircle className="w-4 h-4 text-green-500" />
                {readyCounts} ready
              </span>
              {processingCounts > 0 && (
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4 text-yellow-500" />
                  {processingCounts} processing
                </span>
              )}
            </div>
          )}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : documents?.length === 0 ? (
          <div className="text-center py-10">
            <FileText className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No documents uploaded yet</p>
            <p className="text-xs text-gray-400 mt-1">
              Upload PDF, DOCX, or TXT files to power your chatbot with custom knowledge
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents?.map((doc) => (
              <DocumentRow
                key={doc.id}
                doc={doc}
                onDelete={(id) => deleteMutation.mutate(id)}
                onRefresh={handleRefresh}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

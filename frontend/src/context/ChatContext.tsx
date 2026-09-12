'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent_used?: string | null;
  rich_card?: Record<string, any> | null;
  draft_action_id?: string | null;
  created_at?: string;
  suggested_actions?: string[];
  requires_hitl?: boolean;
  isLoading?: boolean;
}

interface ChatContextType {
  messages: ChatMessage[];
  conversationId: string | null;
  isLoading: boolean;
  sendMessage: (message: string, entityCode: string) => Promise<void>;
  clearChat: () => void;
  loadConversation: (convId: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const CANDIDATE_API_BASES = [
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1\/?$/, ''),
  'http://localhost:8000',
  'http://localhost:8001',
].filter(Boolean) as string[];

let activeApiBase: string | null = null;

async function resolveApiBase(): Promise<string> {
  if (activeApiBase) return activeApiBase;
  for (const base of CANDIDATE_API_BASES) {
    try {
      const res = await fetch(`${base}/health`, { signal: AbortSignal.timeout(800) });
      if (res.ok) {
        const data = await res.json();
        if (data.legal_entities) {
          activeApiBase = base;
          return base;
        }
      }
    } catch {
      // Continue to next candidate
    }
  }
  return 'http://localhost:8001';
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = useCallback(async (message: string, entityCode: string) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };

    const loadingMsg: ChatMessage = {
      id: `loading-${Date.now()}`,
      role: 'assistant',
      content: '',
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setIsLoading(true);

    try {
      const apiBase = await resolveApiBase();
      const token = typeof window !== 'undefined' ? localStorage.getItem('batu_access_token') : null;
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/chat/message`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          entity_code: entityCode,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();

      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      const assistantMsg: ChatMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: data.reply,
        agent_used: data.agent_used,
        rich_card: data.rich_card,
        draft_action_id: data.draft_action_id,
        requires_hitl: data.requires_hitl,
        suggested_actions: data.suggested_actions,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => prev.filter((m) => !m.isLoading).concat(assistantMsg));
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Gagal menghubungi backend: ${err.message || 'Koneksi terputus'}. Pastikan FastAPI berjalan di port 8000.`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => prev.filter((m) => !m.isLoading).concat(errorMsg));
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  const loadConversation = useCallback(async (convId: string) => {
    try {
      const apiBase = await resolveApiBase();
      const res = await fetch(`${apiBase}/api/v1/chat/history/${convId}`);
      if (!res.ok) throw new Error('Failed to load conversation');
      const data = await res.json();
      setConversationId(convId);
      setMessages(
        data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          agent_used: m.agent_used,
          rich_card: m.rich_card,
          draft_action_id: m.draft_action_id,
          created_at: m.created_at,
        }))
      );
    } catch {
      // ignore
    }
  }, []);

  return (
    <ChatContext.Provider value={{ messages, conversationId, isLoading, sendMessage, clearChat, loadConversation }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
}

'use client';

import React, { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({ onSend, disabled = false, placeholder = 'Ketik perintah atau pertanyaan...' }: ChatInputProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [text]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="bg-slate-900/90 backdrop-blur-xl border-t border-slate-700/60 px-4 py-3">
      <div className="max-w-4xl mx-auto flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full bg-slate-800/80 border border-slate-600/60 hover:border-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 text-slate-100 placeholder-slate-500 rounded-xl px-4 py-3 text-sm leading-relaxed resize-none outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
          className="h-11 px-5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl font-bold text-sm shadow-lg shadow-blue-600/20 hover:shadow-blue-500/30 transition-all flex items-center gap-2 shrink-0 disabled:shadow-none disabled:cursor-not-allowed"
        >
          <span>Kirim</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
      <div className="max-w-4xl mx-auto mt-1.5 flex items-center justify-between">
        <span className="text-[10px] text-slate-600">
          Enter untuk kirim • Shift+Enter untuk baris baru
        </span>
      </div>
    </div>
  );
}

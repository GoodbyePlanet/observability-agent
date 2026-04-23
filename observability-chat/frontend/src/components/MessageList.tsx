import { useRef, useEffect } from 'react';
import type { Message } from '../types';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  onSuggestionClick: (message: string) => void;
}

const SUGGESTIONS = [
  'What services are sending traces?',
  'Show me the slowest traces from the last hour',
  'Are there any errors in recent traces?',
  'Show me all error logs',
  'Find me relevant code for ordering coffee',
];

export function MessageList({ messages, onSuggestionClick }: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);

  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    autoScrollRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
  };

  useEffect(() => {
    if (autoScrollRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'instant' });
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <div className="text-center">
          <h2 className="mb-2 text-xl font-semibold text-black">Observability Chat</h2>
          <p className="text-sm text-neutral-500">
            Ask questions about your traces, metrics, and logs
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => onSuggestionClick(s)}
                className="rounded-full border border-neutral-300 px-3 py-1.5 text-xs text-neutral-500 transition-colors hover:border-black hover:text-black"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto px-4 py-6">
      <div className="mx-auto max-w-4xl space-y-4">
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

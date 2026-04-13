import { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled) textareaRef.current?.focus();
  }, [disabled]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-neutral-200 p-4">
      <div className="mx-auto flex max-w-4xl gap-3">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your traces, metrics, or logs..."
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-lg border border-neutral-300 bg-white px-4 py-3 text-black placeholder-neutral-400 focus:border-black focus:outline-none focus:ring-1 focus:ring-black disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          className="rounded-lg bg-black px-5 py-3 font-medium text-white transition-colors hover:bg-neutral-800 disabled:opacity-30 disabled:hover:bg-black"
        >
          Send
        </button>
      </div>
    </div>
  );
}

import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../types';
import { ToolCallCard } from './ToolCallCard';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = memo(function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-br-md bg-black px-4 py-3 text-white">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  const hasContent = message.content.length > 0;
  const hasToolCalls = message.toolCalls.length > 0;

  return (
    <div className="flex justify-start">
      <div className="min-w-0 max-w-[85%]">
        {message.toolCalls.map((tc, i) => (
          <ToolCallCard key={`${tc.name}-${i}`} toolCall={tc} />
        ))}
        {hasContent && (
          <div className="rounded-2xl rounded-bl-md bg-neutral-100 px-4 py-3 text-black">
            <div className="max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  pre({ children }) {
                    return (
                      <pre className="my-2 overflow-x-auto rounded-lg bg-neutral-200 p-3 text-sm [&>code]:bg-transparent [&>code]:p-0">
                        {children}
                      </pre>
                    );
                  },
                  code({ children, className }) {
                    return className ? (
                      <code className="text-black">{children}</code>
                    ) : (
                      <code className="rounded bg-neutral-200 px-1.5 py-0.5 text-sm text-black">
                        {children}
                      </code>
                    );
                  },
                  a({ href, children }) {
                    return (
                      <a href={href} className="underline" target="_blank" rel="noreferrer">
                        {children}
                      </a>
                    );
                  },
                  table({ children }) {
                    return (
                      <div className="my-2 overflow-x-auto">
                        <table className="min-w-full text-sm">{children}</table>
                      </div>
                    );
                  },
                  th({ children }) {
                    return (
                      <th className="border-b border-neutral-300 px-3 py-1.5 text-left font-medium">
                        {children}
                      </th>
                    );
                  },
                  td({ children }) {
                    return (
                      <td className="border-b border-neutral-200 px-3 py-1.5">{children}</td>
                    );
                  },
                  ul({ children }) {
                    return <ul className="ml-4 list-disc space-y-1">{children}</ul>;
                  },
                  ol({ children }) {
                    return <ol className="ml-4 list-decimal space-y-1">{children}</ol>;
                  },
                  p({ children }) {
                    return <p className="mb-2 last:mb-0">{children}</p>;
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        )}
        {!hasContent && !hasToolCalls && (
          <div className="rounded-2xl rounded-bl-md bg-neutral-100 px-4 py-3">
            <div className="flex gap-1">
              <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400 [animation-delay:0ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400 [animation-delay:150ms]" />
              <span className="h-2 w-2 animate-bounce rounded-full bg-neutral-400 [animation-delay:300ms]" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

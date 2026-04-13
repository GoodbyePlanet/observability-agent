import { useState } from 'react';
import type { ToolCall } from '../types';

interface ToolCallCardProps {
  toolCall: ToolCall;
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isRunning = toolCall.status === 'running';

  return (
    <div
      className={`my-2 rounded-lg border ${
        isRunning ? 'border-neutral-300 bg-neutral-50' : 'border-neutral-200 bg-neutral-50'
      }`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm"
      >
        {isRunning ? (
          <span className="inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-neutral-400 border-t-transparent" />
        ) : (
          <span className="shrink-0 text-black">&#10003;</span>
        )}
        <span className="truncate font-mono text-xs text-neutral-600">{toolCall.name}</span>
        <span className="ml-auto shrink-0 text-neutral-400">{expanded ? '\u25BE' : '\u25B8'}</span>
      </button>

      {expanded && (
        <div className="border-t border-neutral-200 px-3 py-2 text-xs">
          <div className="mb-1 text-neutral-400">Arguments</div>
          <pre className="overflow-x-auto rounded bg-neutral-100 p-2 text-neutral-700">
            {JSON.stringify(toolCall.arguments, null, 2)}
          </pre>
          {toolCall.result && (
            <>
              <div className="mb-1 mt-2 text-neutral-400">Result</div>
              <pre className="max-h-60 overflow-x-auto overflow-y-auto rounded bg-neutral-100 p-2 text-neutral-700">
                {toolCall.result}
              </pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}

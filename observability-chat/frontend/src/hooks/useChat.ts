import { useState, useCallback, useRef } from 'react';
import type { Message } from '../types';

interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

async function* parseSSE(response: Response): AsyncGenerator<SSEEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split('\n\n');
      buffer = parts.pop()!;

      for (const part of parts) {
        if (!part.trim()) continue;

        let event = '';
        let data = '';

        for (const line of part.split('\n')) {
          if (line.startsWith('event: ')) event = line.slice(7);
          else if (line.startsWith('data: ')) data = line.slice(6);
        }

        if (event && data) {
          yield { event, data: JSON.parse(data) };
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamingRef = useRef(false);
  const sessionIdRef = useRef('default');

  const sendMessage = useCallback(async (content: string) => {
    if (streamingRef.current) return;
    streamingRef.current = true;
    setIsStreaming(true);

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      toolCalls: [],
    };

    const assistantId = crypto.randomUUID();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      toolCalls: [],
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);

    const updateAssistant = (updater: (msg: Message) => Message) => {
      setMessages(prev =>
        prev.map(m => (m.id === assistantId ? updater(m) : m))
      );
    };

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          session_id: sessionIdRef.current,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      for await (const { event, data } of parseSSE(response)) {
        switch (event) {
          case 'token':
            updateAssistant(m => ({
              ...m,
              content: m.content + (data.content as string),
            }));
            break;

          case 'tool_call_start':
            updateAssistant(m => ({
              ...m,
              toolCalls: [
                ...m.toolCalls,
                {
                  name: data.name as string,
                  arguments: data.arguments as Record<string, unknown>,
                  status: 'running' as const,
                },
              ],
            }));
            break;

          case 'tool_call_end': {
            const toolName = data.name as string;
            const toolResult = data.result as string;
            updateAssistant(m => {
              let matched = false;
              return {
                ...m,
                toolCalls: m.toolCalls.map(tc => {
                  if (!matched && tc.name === toolName && tc.status === 'running') {
                    matched = true;
                    return { ...tc, result: toolResult, status: 'done' as const };
                  }
                  return tc;
                }),
              };
            });
            break;
          }

          case 'error':
            updateAssistant(m => ({
              ...m,
              content: m.content + `\n\n**Error:** ${data.message}`,
            }));
            break;
        }
      }
    } catch (err) {
      updateAssistant(m => ({
        ...m,
        content: `Failed to get response: ${err instanceof Error ? err.message : 'Unknown error'}`,
      }));
    } finally {
      streamingRef.current = false;
      setIsStreaming(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    sessionIdRef.current = crypto.randomUUID();
  }, []);

  return { messages, isStreaming, sendMessage, clearMessages };
}

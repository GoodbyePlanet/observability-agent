import { useChat } from '../hooks/useChat';
import { StatusBar } from './StatusBar';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

export function ChatWindow() {
  const { messages, isStreaming, sendMessage, clearMessages } = useChat();

  return (
    <div className="flex h-full flex-col bg-white text-black">
      <StatusBar onClear={clearMessages} />
      <MessageList messages={messages} onSuggestionClick={sendMessage} />
      <ChatInput onSend={sendMessage} disabled={isStreaming} />
    </div>
  );
}

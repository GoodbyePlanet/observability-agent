export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
  result?: string;
  status: 'running' | 'done';
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls: ToolCall[];
}

export interface McpServerStatus {
  status: 'healthy' | 'unhealthy' | 'disconnected';
  url: string;
  tools?: number;
}

export interface HealthResponse {
  status: string;
  mcp_servers: Record<string, McpServerStatus>;
  llm: { provider: string; model: string };
}
